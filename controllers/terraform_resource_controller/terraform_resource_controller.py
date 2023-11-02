import os
import kopf
import logging
import kubernetes
import json

from ..helpers import update_condition, load_from_yaml, update_array, current_file_path
from .consts import WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME, MANAGED_BY

# Controller configuration
@kopf.on.startup()
def configure(memo: kopf.Memo, settings: kopf.OperatorSettings, **_):
    print('starting up')

    # Log errors as k8s events
    settings.posting.enabled = os.environ.get("EASYAAS_EVENT_ON_ERROR", "0") == "true"
    settings.posting.level = int(os.environ.get("EASYAAS_LOG_LEVEL", logging.ERROR))

    # Initialize the k8s client
    kubernetes.config.load_kube_config(config_file='~/.kube/config', context="k3d-easyaas")
    memo.kubernetes_client = kubernetes.client.api_client.ApiClient()


# Resource the resource config from the CR
terraformresource_config = {}
@kopf.on.event('core.easyaas.dev', 'terraformresource', labels={'managed-by': MANAGED_BY})
def watch_terraformresource(spec, **_):
    terraformresource_config.update(dict(spec))


# Reconcile creates/updates
@kopf.on.create(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
@kopf.on.update(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
def on_change_terraformresource(**ctx):
    # Create a configmap with the terragrun config and resource spec
    configmap = create_configmap(**ctx)
    # Run terragrunt job
    create_job(configmap.metadata.name, **ctx)


# Handle status updates from children
@kopf.on.resume(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
@kopf.on.update(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
def on_status_update_terraformresource(patch, status, **ctx):
    jobs = dict(status.get('jobs', {}))

    conditions = status.get('conditions', [])
    if 'status' not in patch:
        patch['status'] = {}

    # Update the conditions
    ready_status = "False"
    ready_message = ""
    ready_reason = "Initializing"
    for name, job in jobs.items():
        if job.get('failed', None) == True:
            ready_status = 'False'
            ready_message = job['message']
            ready_reason = job['reason']

    ready_condition = {
        'type': 'Ready',
        'status': ready_status,
        'reason': ready_reason,
        'message': ready_message,
    }
    conditions = update_condition(conditions, ready_condition)

    patch['status']['conditions'] = conditions

    # Clean up finished jobs
    for name, job in jobs.items():
        if job.get('active', 0) == 0:
            jobs[name] = None
    patch['status'] = {
        'conditions': conditions,
        'jobs': jobs,
    }


# Reconcile deletes
@kopf.on.delete(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
def on_delete_terraformresource(**ctx):
    # TODO: Implement
    pass


def create_configmap(logger, memo, namespace, name, spec, **_):
    easyaas_resource_params = json.dumps(dict(terraformresource_config['terraform']))
    resource_spec = json.dumps(dict(spec))
    with open('{}/files/terragrunt.hcl'.format(current_file_path()), 'r') as file:
        terragrunt_config = file.read()

    configmap = kubernetes.client.V1ConfigMap(
        metadata=kubernetes.client.V1ObjectMeta(
            generate_name=name,
        ),
        data = {
            'easyaas_resource_params.json': easyaas_resource_params,
            'resource_spec.json': resource_spec,
            'terragrunt.hcl': terragrunt_config
        }
    )
    kopf.adopt([configmap], nested="spec.template", forced=True)
    kopf.label([configmap], {'managed-by': MANAGED_BY})

    return kubernetes.client.CoreV1Api().create_namespaced_config_map(namespace, body=configmap)


def create_job(configmap_name, namespace, **_):
    with open('{}/files/job.yaml'.format(current_file_path()), 'r') as f:
        job = load_from_yaml(f)

    kopf.adopt([job], nested="spec.template", forced=True)
    kopf.label([job], {'managed-by': MANAGED_BY}, nested="spec.template")
    update_array(job.spec.template.spec.volumes,
                 where={'name': 'terragrunt-config'},
                 value=kubernetes.client.V1Volume(
                    name='terragrunt-config',
                    config_map={
                        'name': configmap_name
                    }
                 )
    )

    kubernetes.client.BatchV1Api().create_namespaced_job(namespace, body=job)
