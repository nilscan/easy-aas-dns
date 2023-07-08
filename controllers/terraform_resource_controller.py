import os
import kopf
import logging
import kubernetes
import yaml
import base64
import textwrap
import json

WATCHED_RESOURCE_GROUP = os.environ.get('EASYAAS_WATCHED_RESOURCE_GROUP', 'easyaas.dev')
WATCHED_RESOURCE_NAME = os.environ.get('EASYAAS_WATCHED_RESOURCE_NAME', 'dnsrecord')
RESOURCE_CONFIG_FILE = os.environ.get('EASYAAS_RESOURCE_CONFIG_FILE', 'resources/dns-record/terraformresource.yaml')

with open(RESOURCE_CONFIG_FILE, 'r') as file:
    config = yaml.safe_load(file)

@kopf.on.create(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
@kopf.on.update(WATCHED_RESOURCE_GROUP, WATCHED_RESOURCE_NAME)
def on_change(**ctx):
    configmaps = create_configmap(**ctx)
    if len(configmaps) == 0:
        ctx.logger.info('Error creating configmap')
        return None
    configmap = configmaps[0][0]
    create_job(configmap.metadata.name, **ctx)

    # return {
    #     "ready": True
    # }


def b64encode(str):
    return base64.b64encode(str.encode('ascii')).decode()

def indent(str, amount = 8):
    return textwrap.indent(str, amount * ' ')

def create_configmap(logger, memo, name, spec, **_):
    easyaas_resource_params = json.dumps(dict(config['spec']['terraform']))
    resource_params = json.dumps(dict(spec))
    with open('controllers/files/terragrunt.hcl', 'r') as file:
        terragrunt_config = file.read()

    configmap_spec = textwrap.dedent("""
apiVersion: v1
kind: ConfigMap
metadata:
    generateName: {name}
data:
    easyaas_resource_params.json: |
{easyaas_resource_params}
    resource_params.json: |
{resource_params}
    terragrunt.hcl: |
{terragrunt_config}
    """).format(name=name, easyaas_resource_params=indent(easyaas_resource_params), resource_params=indent(resource_params), terragrunt_config=indent(terragrunt_config))

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
        spec:
            template:
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
    """.format(configmap_name=configmap_name)

    job = yaml.safe_load(job_spec)
    kopf.adopt([job], nested="spec.template", forced=True)

    jobs = kubernetes.utils.create_from_yaml(memo.kubernetes_client, yaml_objects=[job])

    if len(jobs) == 0 or len(jobs[0]) == 0:
        patch['status'] = {
        'conditions': [
                {
                    'lastTransitionTime': '',
                    'type': 'Ready',
                    'status': 'false',
                    'reason': None,
                },
                {
                    'lastTransitionTime': '',
                    'type': 'Failed',
                    'status': 'true',
                    'reason': None,
                }
            ]
        }
        return None

    patch['status'] = {
        'conditions': [
            {
                'lastTransitionTime': '',
                'type': 'Ready',
                'status': 'false',
                'reason': None,
            },
            {
                'lastTransitionTime': '',
                'type': 'InProgress',
                'status': 'true',
                'reason': '{}/{}'.format(jobs[0][0].metadata.namespace, jobs[0][0].metadata.name),
            }
        ]
    }


@kopf.on.startup()
def configure(memo: kopf.Memo, settings: kopf.OperatorSettings, **_):
    print('starting up')

    # Log errors as k8s events
    settings.posting.enabled = os.environ.get("EASYAAS_EVENT_ON_ERROR", "0") == "true"
    settings.posting.level = int(os.environ.get("EASYAAS_LOG_LEVEL", logging.ERROR))

    # Initialize the k8s client
    kubernetes.config.load_kube_config(config_file='~/.kube/config', context="k3d-easyaas")
    memo.kubernetes_client = kubernetes.client.api_client.ApiClient()
