#!/bin/sh
poetry run kopf run -m controllers.audit_controller -m controllers.terraform_resource_controller --log-format=json
