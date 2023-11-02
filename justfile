default:
	@just --choose

build: zip build-docker
local-dev: zip repo-server poetry run

install:
  kubectl apply -f controllers/crds
  kubectl apply -f resources/dns-record

zip:
	local-testing/scripts/zip

build-docker:
  docker build -t easyaas-registry.web:12345/easyaas .; and docker push easyaas-registry.web:12345/easyaas
	cd docker/terragrunt-runner && docker build -t easyaas-registry.web:12345/terragrunt-runner . && docker push easyaas-registry.web:12345/terragrunt-runner

create-k3d-cluster:
	k3d cluster create --config local-testing/k3d/easyaas.yaml

repo-server:
	cd local-testing && docker compose up -d

poetry:
	poetry install

test:
	PYTHONPATH=. poetry run pytest 

run:
	PYTHONPATH=. bin/run_controllers.sh
