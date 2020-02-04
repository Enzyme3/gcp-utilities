# get_compute_count_for_shared_vpc.py
Given a GCP host project id (https://cloud.google.com/vpc/docs/shared-vpc), returns the number of instances deployed in each VPC in that project.

Useful in determining whether VM count is approaching limits:https://cloud.google.com/vpc/docs/quota#per_network

## Usage
python3 get_compute_count_for_shared_vpc.py --project <my_host_project_id>

## Requirements
* gcloud
* python 3.6+
