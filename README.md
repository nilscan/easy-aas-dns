# EasyAaas

EasyAaas (Easy Anything As-A-Service) is a framework to easily create self-service infrastructure resources.
It lets Platform Engineers create Resources that Developers can instanciate at will.

A Resource is a composed of a few elements:

* A kubernetes CRD that defines a name and the configuration parameters available for the Resource.
* A terraform module that defines what needs to be done when applying the resource
* A TerraformResource yaml that instanciates a new kubernetes controller to watch over the Resource and that will apply the terraform module
* Optionally, OPA policies and version conversion functions can be provided to handle complex validation and migration scenarios

## Setup

```shell

pip install poetry
poetry shell
poetry install
```

## Run

```shell
make run
```
