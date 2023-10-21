import os
import kopf
import logging
import kubernetes
import yaml


@kopf.on.create('core.easyaas.dev', 'terraformresource')
@kopf.on.update('core.easyaas.dev', 'terraformresource')
def on_change(logger, memo: kopf.Memo, patch, **_):
    """
    Deploy a new Terraform Resource controller

    This will run a new kopf deployment of `terraform_resource_controller` to
    watch over a specific CRD and run terraform to apply changes to it
    """
    pass

@kopf.on.startup()
def configure(memo: kopf.Memo, settings: kopf.OperatorSettings, **_):
    print('starting up')

    # Log errors as k8s events
    settings.posting.enabled = os.environ.get("EASYAAS_EVENT_ON_ERROR", "0") == "true"
    settings.posting.level = int(os.environ.get("EASYAAS_LOG_LEVEL", logging.ERROR))

    # Initialize the k8s client
    kubernetes.config.load_kube_config(config_file='~/.kube/config', context="k3d-ingress")
    memo.kubernetes_client = kubernetes.client.api_client.ApiClient()
