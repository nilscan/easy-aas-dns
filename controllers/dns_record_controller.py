import os
import kopf
import logging
import kubernetes
import yaml


@kopf.on.create('easyaas.dev', 'dnsrecord')
@kopf.on.update('easyaas.dev', 'dnsrecord')
def on_change(logger, memo: kopf.Memo, patch, **_):
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
                          image: cytopia/terragrunt
                          command: ["sh", "-c", "tfswitch && terraform plan"]
                    restartPolicy: Never
            backoffLimit: 0
            ttlSecondsAfterFinished: 3600
    """

    job = yaml.safe_load(job_spec)
    kopf.adopt([job], nested="spec.template", forced=True)

    jobs = kubernetes.utils.create_from_yaml(memo.kubernetes_client, yaml_objects=[job])
    logger.info(jobs)

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
    # return {
    #     "ready": True
    # }


@kopf.on.startup()
def configure(memo: kopf.Memo, settings: kopf.OperatorSettings, **_):
    print('starting up')

    # Log errors as k8s events
    settings.posting.enabled = os.environ.get("EASYAAS_EVENT_ON_ERROR", "0") == "true"
    settings.posting.level = int(os.environ.get("EASYAAS_LOG_LEVEL", logging.ERROR))

    # Initialize the k8s client
    kubernetes.config.load_kube_config(config_file='~/.kube/config', context="k3d-ingress")
    memo.kubernetes_client = kubernetes.client.api_client.ApiClient()