build: zip build-docker

zip:
	scripts/zip

build-docker:
	cd docker/terragrunt-runner && docker build -t easyaas-registry.web:12345/terragrunt-runner . && docker push easyaas-registry.web:12345/terragrunt-runner

repo-server:
	cd local-testing && docker compose up -d

poetry:
	poetry install

local-dev: zip repo-server poetry
	poetry run kopf run controllers/*_controller.py --log-format=json
