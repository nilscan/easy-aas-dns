#!/bin/sh
poetry run kopf run --all-namespaces -m controllers.terraform_resource_controller --log-format=json --liveness=http://0.0.0.0:8080/healthz
