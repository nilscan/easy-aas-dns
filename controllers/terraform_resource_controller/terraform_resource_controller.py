import os
import kopf
import logging
import kubernetes
import json
import subprocess

from ..helpers import update_condition, load_from_yaml, update_array, current_file_path
from .consts import WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME, MANAGED_BY, EASYAAS_PREFIX

# Controller configuration
@kopf.on.startup()
def configure(memo: kopf.Memo, settings: kopf.OperatorSettings, **_):
    print('starting up')

    # Log errors as k8s events
    settings.posting.enabled = os.environ.get("EASYAAS_EVENT_ON_ERROR", "0") == "true"
    settings.posting.level = int(os.environ.get("EASYAAS_LOG_LEVEL", logging.ERROR))

    # Initialize the k8s client
    try:
        kubernetes.config.load_incluster_config()
    except kubernetes.config.ConfigException:
        kubernetes.config.load_kube_config(config_file='~/.kube/config', context="k3d-easyaas")


# Read the resource config from the CR
terraformresource_config = {}
@kopf.on.event('core.easyaas.dev', 'terraformresources', field='metadata.name', value=WATCHED_RESOURCE_NAME)
def watch_terraformresource(spec, **_):
    terraformresource_config.update(dict(spec))


# Reconcile creates/updates
@kopf.on.create(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
@kopf.on.update(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
def on_change_terraformresource(namespace, name, body, meta, spec, **_):
    # Read the terragrunt.hcl from file
    with open('{}/files/terragrunt.hcl'.format(current_file_path()), 'r') as file:
        terragrunt_config = file.read()

    helm_values = {
        'name': name,
        'managedBy': MANAGED_BY,
        'easyaasResourceParams': dict(terraformresource_config),
        'resource': dict(body),
        'resourceMeta': dict(meta),

        # Inject additional values to the resource spec
        # This will be added to the terraform.tfvars but doesn't cause issues
        # if the template doesn't define the corresponding variables
        'resourceSpec': dict(spec).update({
            'metadataName':  meta.name,
            'metadataNamespace': meta.namespace,
            'metadataLabels': dict(meta.labels),
            'metadataAnnotations': dict(meta.annotations),
        }),
        'terragrunt': terragrunt_config,
    }

    subprocess.run(
        [
            "helm", "upgrade", "--install",
            "{}-{}".format(EASYAAS_PREFIX, name),
            '{}/charts/terraform-job'.format(current_file_path()),
            '--debug',
            '--namespace', namespace,
            '--values', '-', # Send values via stdin
        ],
        check=True,
        input=json.dumps(helm_values).encode('utf-8'),
    )


# Reconcile deletes
@kopf.on.delete(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
def on_delete_terraformresource(namespace, name, **_):
    subprocess.run(
        [
            "helm", "uninstall", 
            "{}-{}".format(EASYAAS_PREFIX, name),
            '--debug',
            '--namespace', namespace,
        ],
        check=True,
    )


# Handle status updates from children
@kopf.on.resume(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
@kopf.on.update(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
def on_status_update_terraformresource(patch, status, **_):
    jobs = dict(status.get('jobs', {}))

    conditions = status.get('conditions', [])
    if 'status' not in patch:
        patch['status'] = {}

    # Update the conditions
    ready_condition = {
        'type': 'Ready',
        'status': 'False',
        'reason': 'Initializing',
        'message': '',
    }
    for name, job in jobs.items():
        if job.get('failed', None) == True:
            ready_condition.update({
                'status': 'False',
                'reason': job['reason'],
                'message': job['message'],
            })

    conditions = update_condition(conditions, ready_condition)

    # Clean up finished jobs
    for name, job in jobs.items():
        if job.get('active', 0) == 0:
            jobs[name] = None

    patch['status'] = {
        'conditions': conditions,
        'jobs': jobs,
    }
