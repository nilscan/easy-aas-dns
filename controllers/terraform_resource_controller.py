import os
import kopf
import logging
import kubernetes
import yaml
import base64
import textwrap
import json

from .helpers import current_timestamp, update_condition
from .consts import JOB_FINALIZER

WATCHED_RESOURCE_GROUP = os.environ.get('EASYAAS_WATCHED_RESOURCE_GROUP', 'easyaas.dev')
WATCHED_RESOURCE_NAME = os.environ.get('EASYAAS_WATCHED_RESOURCE_NAME', 'dnsrecords')
RESOURCE_CONFIG_FILE = os.environ.get('EASYAAS_RESOURCE_CONFIG_FILE', 'resources/dns-record/terraformresource.yaml')

MANAGED_BY = '{}.{}'.format(WATCHED_RESOURCE_NAME, WATCHED_RESOURCE_GROUP)

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

    # Setup server for admission webhooks for local dev
    # TODO: Setup protection to avoid webhooks from being created in non-local clusters
    # if os.environ.get('ENVIRONMENT') is 'k3d':
    #     settings.admission.server = kopf.WebhookK3dServer(port=54321)
    #     settings.admission.managed = 'auto.kopf.dev'
    # else:
    #     settings.admission.server = kopf.WebhookServer(addr='0.0.0.0', port=8080)
    #  #     settings.admission.managed = 'auto.kopf.dev' # Disable as we don't want easyaas to create webhooks automatically


# Resource the resource config from the CR
terraformresource_config = {}
@kopf.on.event('core.easyaas.dev', 'terraformresource', labels={'managed-by': MANAGED_BY})
def watch_terraformresource(spec, **_):
    terraformresource_config.update(dict(spec))

# Watch terragrunt jobs
@kopf.on.event('batch/v1', 'job', labels={'managed-by': MANAGED_BY})
def watch_job(logger, meta: kopf.Meta, namespace, name, status: kopf.Status, **_):
    # Get the owner resource
    ownerRefs = meta.get('ownerReferences', {})
    ctrlOwners = [ owner for owner in ownerRefs if owner.get('controller', False) == True ]
    if len(ctrlOwners) != 1:
        logger.debug("No Controller owner found, skipping")
        return
    
    owner = ctrlOwners[0]
    crdapi = kubernetes.client.CustomObjectsApi()
    (group, version) = owner.get('apiVersion', "").split("/")

    status = dict(status)

    if meta.deletion_timestamp is not None:
        # If the job is being deleted, remove it from the status
        job_status = {
            name: {
                'deleted': True
            }
        }
        # Remove the finalizer
        api = kubernetes.client.BatchV1Api()
        finalizer_index = meta.get('finalizers', []).index(JOB_FINALIZER)
        logger.info('finalizer index: {}'.format(finalizer_index))
        try:
            api.patch_namespaced_job(
                name=name,
                namespace=namespace,
                body=[{
                    'op': 'remove',
                    'path': '/metadata/finalizers/{}'.format(finalizer_index)
                }]
            )
        except kubernetes.client.exceptions.ApiException:
            pass
    else:
        reason = None
        message = None
        for cond in status.get('conditions', []):
            if cond.get('type', '') == 'Failed' and cond.get('status', '') == "True":
                reason = cond.get('reason', '')
                message = cond.get('message', '')
        job_status = {
            name: {
                'job': '{}/{}'.format(namespace, name),
                'active': status.get('active', 0),
                'failed': True if status.get('failed', 0) > 0 else False,
                'reason': reason,
                'message': message,
            }
        }

    
    job_status[name]['lastTransitionTime'] = current_timestamp()

    try:
        crdapi.patch_namespaced_custom_object_status(
            group=group,
            version=version,
            plural=WATCHED_RESOURCE_NAME,
            name=owner['name'],
            namespace=namespace,
            body={
                'status': {
                    'jobs': job_status
                }
            }
        )
    except kubernetes.client.exceptions.ApiException as e:
        if e.status == 404:
            # This can happen if the parent gets deleted
            # and the garbage collection deletes the child jobs
            # It's safe to ignore it
            return


# TODO: Implement OPA validation
# @kopf.on.validate(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
# def on_validate_terraformresource(warnings: list[str], **_):
#     warnings.append("Validation webhook Not implemented")
#     if False:
#         raise kopf.AdmissionError("Not Implemented")

# Reconcile creates/updates
@kopf.on.create(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
@kopf.on.update(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
def on_change_terraformresource(**ctx):
    # Create a configmap with the terragrun config and resource spec
    configmaps = create_configmap(**ctx)
    if len(configmaps) == 0:
        ctx.logger.info('Error creating configmap')
        return None
    configmap = configmaps[0][0]

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
    ready_status = ""
    ready_message = ""
    ready_reason = ""
    for name, job in jobs.items():
        if job['failed'] == True:
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

def b64encode(str):
    return base64.b64encode(str.encode('ascii')).decode()

def indent(str, amount = 8):
    return textwrap.indent(str, amount * ' ')

def create_configmap(logger, memo, name, spec, **_):
    easyaas_resource_params = json.dumps(dict(terraformresource_config['terraform']))
    resource_spec = json.dumps(dict(spec))
    with open('controllers/files/terragrunt.hcl', 'r') as file:
        terragrunt_config = file.read()

    configmap_spec = textwrap.dedent("""
apiVersion: v1
kind: ConfigMap
metadata:
    generateName: {name}
    labels:
      managed-by: {managed_by}
data:
    easyaas_resource_params.json: |
{easyaas_resource_params}
    resource_spec.json: |
{resource_spec}
    terragrunt.hcl: |
{terragrunt_config}
    """).format(name=name, managed_by=MANAGED_BY, easyaas_resource_params=indent(easyaas_resource_params), resource_spec=indent(resource_spec), terragrunt_config=indent(terragrunt_config))

    logger.info(configmap_spec)

    configmap = yaml.safe_load(configmap_spec)
    kopf.adopt([configmap], nested="spec.template", forced=True)
    return kubernetes.utils.create_from_yaml(memo.kubernetes_client, yaml_objects=[configmap])

def create_job(configmap_name, memo, patch, **_):
    job_spec = """
        apiVersion: batch/v1
        kind: Job
        metadata:
            name: terraform
            labels:
                managed-by: {managed_by}
            finalizers:
                - {job_finalizer}
        spec:
            template:
                metadata:
                    labels:
                        managed-by: {managed_by}
                spec:
                    containers:
                        - name: tf
                          image: easyaas-registry.web:12345/terragrunt-runner
                          imagePullPolicy: Always
                          env:
                            - name: TERRAGRUNT_CONFIG
                              value: /app/terragrunt-config/terragrunt.hcl
                          volumeMounts:
                            - name: terragrunt-config
                              mountPath: /app/terragrunt-config

                    restartPolicy: Never
                    volumes:
                      - name: terragrunt-config
                        configMap:
                          name: {configmap_name}
            backoffLimit: 0
            ttlSecondsAfterFinished: 3600
    """.format(managed_by=MANAGED_BY, job_finalizer=JOB_FINALIZER, configmap_name=configmap_name)

    job = yaml.safe_load(job_spec)
    kopf.adopt([job], nested="spec.template", forced=True)

    kubernetes.utils.create_from_yaml(memo.kubernetes_client, yaml_objects=[job])
