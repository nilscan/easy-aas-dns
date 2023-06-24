zip:
	scripts/zip

repo-server:
	cd reposerver
	docker compose -f reposerver/docker-compose.yaml up -d

poetry:
	poetry install

local-dev: zip repo-server poetry
	poetry run kopf run controllers/*.py --log-format=json
