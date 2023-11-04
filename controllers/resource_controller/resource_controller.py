import os
import kopf
import logging
from ..helpers import update_condition, load_from_yaml, update_array, current_file_path
import subprocess

@kopf.on.startup()
def configure(memo: kopf.Memo, settings: kopf.OperatorSettings, **_):
    print('starting up')

    # Log errors as k8s events
    settings.posting.enabled = os.environ.get("EASYAAS_EVENT_ON_ERROR", "0") == "true"
    settings.posting.level = int(os.environ.get("EASYAAS_LOG_LEVEL", logging.ERROR))


@kopf.on.create('core.easyaas.dev', 'terraformresources')
@kopf.on.update('core.easyaas.dev', 'terraformresources')
def on_change(namespace, name, spec, **_):
    """
    Deploy a new Terraform Resource controller

    This will run a new kopf deployment of `terraform_resource_controller` to
    watch over a specific CRD and run terraform to apply changes to it
    """
    # Install the helm chart
    # FIXME: This should be done in a job
    [plural, *group] = spec['crd'].split('.')
    group = '.'.join(group)
    subprocess.run(
        [
            "helm", "upgrade", "--install",
            name,
            '{}/charts/resource-controller'.format(current_file_path()),
            '--namespace', namespace,
            '--set', 'resource.group={}'.format(group),
            '--set', 'resource.name={}'.format(plural),
        ],
        check=True,
    )


@kopf.on.delete('core.easyaas.dev', 'terraformresources')
def on_change(namespace, name, spec, **_):
    """
    Undeploy a new Terraform Resource controller

    This will delete the controller for the specified resource
    """
    [plural, *group] = spec['crd'].split('.')
    group = '.'.join(group)
    subprocess.run(
        [
            "helm", "uninstall",
            name,
            '--namespace', namespace,
        ],
        check=True,
    )
    