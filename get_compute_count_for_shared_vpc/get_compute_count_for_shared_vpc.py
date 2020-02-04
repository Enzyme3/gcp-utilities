"""Get Compute Count for Shared VPC

Given a GCP host project id (https://cloud.google.com/vpc/docs/shared-vpc),
returns the number of instances deployed in each VPC in that project.

Useful in determining whether VM count is apprpoaching limits:
https://cloud.google.com/vpc/docs/quota#per_network


Example:
    $ python3 get_compute_count_for_shared_vpc.py --project <my_host_project_id>
"""
import argparse
from collections import defaultdict
import csv
from datetime import datetime
import subprocess
import sys

OUTPUT_SUMMARY_CSV_NAME = f'shared_vpc_copmute_count_results_summmary_{datetime.now():%Y-%m-%d-%H_%M_%S}.csv'
OUTPUT_DETAILED_CSV_NAME = f'shared_vpc_compute_count_results_detailed_{datetime.now():%Y-%m-%d-%H_%M_%S}.csv'

parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
required = parser.add_argument_group('required arguments')
required.add_argument('--project', help='Your Google Cloud host project ID', required=True)
args = parser.parse_args()
host_project = args.project

# get service projects attached to host project
get_service_projects_cmd = ('gcloud compute shared-vpc associated-projects list'
                            f' --project {host_project} --format="value(id)"')
get_service_projects_cmd_result = subprocess.check_output(get_service_projects_cmd, shell=True)
projects = get_service_projects_cmd_result.decode(sys.stdout.encoding).strip().split('\n')

# add host project to list of sprojects
if (len(projects) == 1 and not projects[0]):
  projects[0] = host_project
else:
  projects.append(host_project)

# get VPCs in host project
get_vpcs_cmd = f'gcloud compute networks list --project {host_project} --format="value(name)"'
get_vpcs_cmd_result = subprocess.check_output(get_vpcs_cmd, shell=True)
vpcs = get_vpcs_cmd_result.decode(sys.stdout.encoding).strip().split('\n')

if (len(vpcs) == 0) or (len(vpcs) == 1 and not vpcs[0]):
  sys.exit('No VPCs in host project')

count_by_project_by_network = defaultdict(lambda: defaultdict(int))
count_by_network = defaultdict(int)

network_filter = f'https://www.googleapis.com/compute/v1/projects/{host_project}/'

# iterate thru each project, and grab list of instances deployed to shared vpc
for project in projects:
  get_instances_cmd = (f'gcloud compute instances list --project {project}'
                       f' --filter="networkInterfaces.network: {network_filter}"'
                       ' --format="value(networkInterfaces.network)" | '
                       'sort | uniq -c')
  get_instances_result = subprocess.check_output(get_instances_cmd, shell=True).strip()
  instances = get_instances_result.decode(sys.stdout.encoding).strip().split('\n')

  if (not instances) or (len(instances) == 1 and not instances[0]):
    continue

  for instance in instances:
    instance = instance.strip()
    count, network = instance.split(" ")
    count = int(count)
    network = network.rsplit("/", 1)[1]

    count_by_project_by_network[network][project] += count
    count_by_network[network] += count

with open(OUTPUT_DETAILED_CSV_NAME, 'w', newline='') as csv_file:
  writer = csv.writer(csv_file)
  writer.writerow(["Shared VPC Network", "Project Id", "VM Count"])

  for network, count_by_project in count_by_project_by_network.items():
    for project, count in count_by_project.items():
      writer.writerow([network, project, count])

with open(OUTPUT_SUMMARY_CSV_NAME, 'w', newline='') as csv_file:
  writer = csv.writer(csv_file)
  writer.writerow(["Shared VPC Network", "VM Count"])
  print('Shared VPC Network,VM Count')

  for network, count in count_by_network.items():
    writer.writerow([network, count])
    print(f'{network},{count}')
