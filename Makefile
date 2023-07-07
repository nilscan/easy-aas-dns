zip:
	scripts/zip

repo-server:
	cd local-testing && docker compose up -d

poetry:
	poetry install

local-dev: zip repo-server poetry
	poetry run kopf run controllers/*.py --log-format=json
