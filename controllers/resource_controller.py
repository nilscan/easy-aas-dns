import os
import kopf
import logging
import kubernetes
import yaml


@kopf.on.create('easyaas.dev', 'terraformresource')
@kopf.on.update('easyaas.dev', 'terraformresource')
def on_change(logger, memo: kopf.Memo, patch, **_):
    """
    Deploy a new Terraform Resource controller

    This will run a new kopf deployment of `terraform_resource_controller` to
    watch over a specific CRD and run terraform to apply changes to it
    """
    job_spec = """
        apiVersion: apps/v1
        kind: Job
        metadata:
            name: 
        spec:
            template:
                spec:
                    containers:
                        - name: tf
                          image: cytopia/terragrunt
                          command: ["sh", "-c", "tfswitch && terragrunt apply --auto-approve"]
                    restartPolicy: Never
            backoffLimit: 0
            ttlSecondsAfterFinished: 3600
    """

    job = yaml.safe_load(job_spec)
    kopf.adopt([job], nested="spec.template", forced=True)

    jobs = kubernetes.utils.create_from_yaml(memo.kubernetes_client, yaml_objects=[job])
    logger.info(jobs)


@kopf.on.startup()
def configure(memo: kopf.Memo, settings: kopf.OperatorSettings, **_):
    print('starting up')

    # Log errors as k8s events
    settings.posting.enabled = os.environ.get("EASYAAS_EVENT_ON_ERROR", "0") == "true"
    settings.posting.level = int(os.environ.get("EASYAAS_LOG_LEVEL", logging.ERROR))

    # Initialize the k8s client
    kubernetes.config.load_kube_config(config_file='~/.kube/config', context="k3d-ingress")
    memo.kubernetes_client = kubernetes.client.api_client.ApiClient()