# EasyAaas

EasyAaas (Easy Anything As-A-Service) is a framework to easily create self-service infrastructure resources.
It lets Platform Engineers create Resources that Developers can instanciate at will.

A Resource is a composed of a few elements:

* A kubernetes CRD that defines a name and the configuration parameters available for the Resource.
* A terraform module that defines what needs to be done when applying the resource
* A TerraformResource yaml that instanciates a new kubernetes controller to watch over the Resource and that will apply the terraform module
* Optionally, OPA policies and version conversion functions can be provided to handle complex validation and migration scenarios

## Setup

### Install Easyaas

```shell

pip install poetry
poetry shell
poetry install
```

### Install opa-kubemgmt

Validation of the CRDs can be done by any admission controller.
This is an example using [open-policy-agent/kube-mgmt](https://github.com/open-policy-agent/kube-mgmt)

```shell
helm repo add opa https://open-policy-agent.github.io/kube-mgmt/charts
helm repo update
helm upgrade --install --namespace opa-kubemgmt --create-namespace opa-kubemgmt opa/opa-kube-mgmt --set admissionController.enabled=true --set mgmt.namespaces=easyaas-policies --set admissionController.failurePolicy=Fail
```

## Run

EasyAas uses [just](https://github.com/casey/just) to define and run project-related commands

```shell
just run
```
