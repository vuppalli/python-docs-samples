import os, uuid
from google.cloud import dataproc_v1 as dataproc
from google.cloud import storage

waiting_callback = False

# Set variables
project = os.environ['GCLOUD_PROJECT']
region = "us-central1"
zone = "us-central1-a"
cluster_name = 'setup-test-{}'.format(str(uuid.uuid4()))


def test_setup(capsys):
    '''Create GCS Bucket'''
    storage_client = storage.Client()
    bucket_name = 'setup-test-code-{}'.format(str(uuid.uuid4()))
    bucket = storage_client.create_bucket(bucket_name)

    '''Upload file'''
    destination_blob_name = "setup.py"
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename("setup.py")

    job_file_name = "gs://" + bucket_name + "/setup.py"

    '''Create Cluster'''
    zone_uri = \
        'https://www.googleapis.com/compute/v1/projects/{}/zones/{}'.format(
            project, zone)
    cluster_data = {
        'project_id': project,
        'cluster_name': cluster_name,
        'config': {
            'gce_cluster_config': {
                'zone_uri': zone_uri
            },
            'master_config': {
                'num_instances': 1,
                'machine_type_uri': 'n1-standard-1'
            },
            'worker_config': {
                'num_instances': 2,
                'machine_type_uri': 'n1-standard-1'
            }
        }
    }

    cluster_client = dataproc.ClusterControllerClient(client_options={
        'api_endpoint': '{}-dataproc.googleapis.com:443'.format(region)
    })
    cluster = cluster_client.create_cluster(project, region, cluster_data)
    cluster.add_done_callback(callback)
    global waiting_callback
    waiting_callback = True

    '''Submit job'''
    job_details = {
        'placement': {
            'cluster_name': cluster_name
        },
        'pyspark_job': {
            'main_python_file_uri': job_file_name
        }
    }

    job_client = dataproc.JobControllerClient(client_options={
        'api_endpoint': '{}-dataproc.googleapis.com:443'.format(region)
    })
    result = job_client.submit_job(project_id=project, region=region, job=job_details)
    job_id = result.reference.job_id


def callback(operation_future):
    global waiting_callback
    waiting_callback = False

