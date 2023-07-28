build: zip build-docker
local-dev: zip repo-server poetry run

zip:
	local-testing/scripts/zip

build-docker:
	cd docker/terragrunt-runner && docker build -t easyaas-registry.web:12345/terragrunt-runner . && docker push easyaas-registry.web:12345/terragrunt-runner

create-k3d-cluster:
	k3d cluster create --config local-testing/k3d/easyaas.yaml

repo-server:
	cd local-testing && docker compose up -d

poetry:
	poetry install

test:
	PYTHONPATH=. pytest 

run:
	PYTHONPATH=. poetry run kopf run -m controllers.audit_controller -m controllers.terraform_resource_controller --log-format=json
