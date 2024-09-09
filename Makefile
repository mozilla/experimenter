SHELL = /bin/bash

WAIT_FOR_DB = /experimenter/bin/wait-for-it.sh -t 30 db:5432 &&
WAIT_FOR_RUNSERVER = /experimenter/bin/wait-for-it.sh -t 30 localhost:7001 &&

COMPOSE_CIRRUS = [[ -n $$CIRRUS ]] && echo "-f docker-compose-cirrus.yml"
COMPOSE = docker compose -f docker-compose.yml $$(${COMPOSE_CIRRUS})
COMPOSE_LEGACY = ${COMPOSE} -f docker-compose-legacy.yml
COMPOSE_TEST = docker compose -f docker-compose-test.yml
COMPOSE_PROD = docker compose -f docker-compose-prod.yml $$(${COMPOSE_CIRRUS})
COMPOSE_INTEGRATION = ${COMPOSE_PROD} -f docker-compose-integration-test.yml $$(${COMPOSE_CIRRUS})
DOCKER_BUILD = docker buildx build

JOBS = 4
PARALLEL = parallel --halt now,fail=1 --jobs ${JOBS} {} :::
NOCOLOR= \033[0m
RED = \033[0;31m
GREEN = \033[0;32m
PAD = -------------------------------------------------\n
COLOR_CHECK = && echo "${GREEN}${PAD}All Checks Passed\n${PAD}${NOCOLOR}" || (echo "${RED}${PAD}Some Checks Failed\n${PAD}${NOCOLOR}";exit 1)
PYTHON_TEST = pytest --cov --cov-report term-missing
PYTHON_TYPECHECK = pyright experimenter/
PYTHON_CHECK_MIGRATIONS = python manage.py makemigrations --check --dry-run --noinput
PYTHON_MIGRATE = python manage.py migrate
ESLINT_LEGACY = yarn workspace @experimenter/core lint
ESLINT_FIX_CORE = yarn workspace @experimenter/core lint-fix
ESLINT_NIMBUS_UI = yarn workspace @experimenter/nimbus-ui lint
ESLINT_FIX_NIMBUS_UI = yarn workspace @experimenter/nimbus-ui lint-fix
ESLINT_NIMBUS_UI_NEW = yarn workspace @experimenter/nimbus_ui_new lint
ESLINT_FIX_NIMBUS_UI_NEW = yarn workspace @experimenter/nimbus_ui_new format
TYPECHECK_NIMBUS_UI = yarn workspace @experimenter/nimbus-ui lint:tsc
DJLINT_CHECK = djlint --check experimenter/nimbus_ui_new/
DJLINT_FIX = djlint --reformat experimenter/nimbus_ui_new/
JS_TEST_LEGACY = yarn workspace @experimenter/core test
JS_TEST_NIMBUS_UI = DEBUG_PRINT_LIMIT=999999 CI=yes yarn workspace @experimenter/nimbus-ui test:cov
NIMBUS_SCHEMA_CHECK = python manage.py graphql_schema --out experimenter/nimbus-ui/test_schema.graphql&&diff experimenter/nimbus-ui/test_schema.graphql experimenter/nimbus-ui/schema.graphql || (echo GraphQL Schema is out of sync please run make generate_types;exit 1)
NIMBUS_TYPES_GENERATE = python manage.py graphql_schema --out experimenter/nimbus-ui/schema.graphql&&yarn workspace @experimenter/nimbus-ui generate-types
RUFF_CHECK = ruff check experimenter/ tests/
RUFF_FIX = ruff check --fix experimenter/ tests/
BLACK_CHECK = black -l 90 --check --diff . --exclude node_modules
BLACK_FIX = black -l 90 . --exclude node_modules
CHECK_DOCS = python manage.py generate_docs --check=true
GENERATE_DOCS = python manage.py generate_docs
LOAD_COUNTRIES = python manage.py loaddata ./experimenter/base/fixtures/countries.json
LOAD_LOCALES = python manage.py loaddata ./experimenter/base/fixtures/locales.json
LOAD_LANGUAGES = python manage.py loaddata ./experimenter/base/fixtures/languages.json
LOAD_FEATURES = python manage.py load_feature_configs
LOAD_DUMMY_EXPERIMENTS = [[ -z $$SKIP_DUMMY ]] && python manage.py load_dummy_experiments || python manage.py load_dummy_projects


JETSTREAM_CONFIG_URL = https://github.com/mozilla/metric-hub/archive/main.zip

CLI_DIR = experimenter/experimenter/features/manifests/application-services
CLI_INSTALLER = $(CLI_DIR)/install-nimbus-cli.sh
NIMBUS_CLI = $(CLI_DIR)/nimbus-cli

help:
	@echo "Please use 'make <target>' where <target> is one of the following commands."
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Check the Makefile to know exactly what each target is doing."

ssl: nginx/key.pem nginx/cert.pem  ## Generate all SSL certificates

nginx/key.pem:
	openssl genrsa -out nginx/key.pem 4096

nginx/cert.pem: nginx/key.pem
	openssl req -new -x509 -nodes -sha256 -key nginx/key.pem \
		-subj "/C=US/ST=California/L=Mountain View/O=Mozilla/CN=experiment_local" \
		> nginx/cert.pem

secretkey:  ## Generate random key
	openssl rand -hex 24

auth_gcloud:  ## Login to GCloud
	gcloud auth login --update-adc

jetstream_config:
	curl -LJ -o experimenter/experimenter/outcomes/metric-hub.zip $(JETSTREAM_CONFIG_URL)
	unzip -o -d experimenter/experimenter/outcomes experimenter/experimenter/outcomes/metric-hub.zip
	rm -Rf experimenter/experimenter/outcomes/metric-hub-main/.script/
	unzip -o -d experimenter/experimenter/segments experimenter/experimenter/outcomes/metric-hub.zip
	rm -Rf experimenter/experimenter/segments/metric-hub-main/.script/

feature_manifests: build_dev
	$(COMPOSE) run -e GITHUB_BEARER_TOKEN=$(GITHUB_BEARER_TOKEN) experimenter /experimenter/bin/manifest-tool.py fetch $(FETCH_ARGS)

install_nimbus_cli:  ## Install Nimbus client
	mkdir -p $(CLI_DIR)
	curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/mozilla/application-services/main/install-nimbus-cli.sh > "$(CLI_INSTALLER)"
	$(SHELL) $(CLI_INSTALLER) --directory "$(CLI_DIR)"

fetch_external_resources: jetstream_config install_nimbus_cli feature_manifests  ## Fetch all external resources
	echo "External Resources Fetched"

update_kinto:  ## Update latest Kinto/Remote Settings container
	docker pull mozilla/kinto-dist:latest

compose_build:  ## Build containers
	$(COMPOSE) build

build_megazords:
	$(DOCKER_BUILD) -f application-services/Dockerfile -t experimenter:megazords application-services/

update_application_services: build_megazords
	docker run \
		-v ./application-services/application-services.env:/application-services/application-services.env \
		experimenter:megazords \
		/application-services/update-application-services.sh

build_dev: ssl build_megazords
	$(DOCKER_BUILD) --target dev -f experimenter/Dockerfile -t experimenter:dev experimenter/

build_integration_test: ssl build_megazords
	$(DOCKER_BUILD) -f experimenter/tests/integration/Dockerfile -t experimenter:integration-tests experimenter/

build_test: ssl build_megazords
	$(DOCKER_BUILD) --target test -f experimenter/Dockerfile -t experimenter:test experimenter/

build_ui: ssl
	$(DOCKER_BUILD) --target ui -f experimenter/Dockerfile -t experimenter:ui experimenter/

build_prod: ssl build_megazords
	$(DOCKER_BUILD) --target deploy -f experimenter/Dockerfile -t experimenter:deploy experimenter/

compose_stop:
	$(COMPOSE) kill || true
	$(COMPOSE_INTEGRATION) kill || true
	$(COMPOSE_PROD) kill || true

compose_rm:
	$(COMPOSE) rm -f -v || true
	$(COMPOSE_INTEGRATION) rm -f -v || true
	$(COMPOSE_PROD) rm -f -v || true

docker_prune:
	docker container prune -f
	docker image prune -f
	docker volume prune -f
	docker volume rm $$(docker volume ls -qf dangling=true) || true

static_rm:  ## Remove statically generated files
	rm -Rf experimenter/node_modules
	rm -Rf experimenter/experimenter/legacy/legacy-ui/core/node_modules/
	rm -Rf experimenter/experimenter/nimbus-ui/node_modules/
	rm -Rf experimenter/experimenter/legacy/legacy-ui/assets/
	rm -Rf experimenter/experimenter/nimbus-ui/build/

kill: compose_stop compose_rm docker_prune  ## Stop, remove, and prune containers
	echo "All containers removed!"

lint: build_test  ## Running linting on source code
	$(COMPOSE_TEST) run experimenter sh -c '$(WAIT_FOR_DB) (${PARALLEL} "$(NIMBUS_SCHEMA_CHECK)" "$(PYTHON_CHECK_MIGRATIONS)" "$(CHECK_DOCS)" "$(BLACK_CHECK)" "$(RUFF_CHECK)" "$(DJLINT_CHECK)" "$(ESLINT_LEGACY)" "$(ESLINT_NIMBUS_UI)" "$(ESLINT_NIMBUS_UI_NEW)" "$(TYPECHECK_NIMBUS_UI)" "$(PYTHON_TYPECHECK)" "$(PYTHON_TEST)" "$(JS_TEST_LEGACY)" "$(JS_TEST_NIMBUS_UI)" "$(JS_TEST_REPORTING)") ${COLOR_CHECK}'
check: lint

test: build_test  ## Run tests
	$(COMPOSE_TEST) run experimenter sh -c '$(WAIT_FOR_DB) $(PYTHON_TEST)'
pytest: test

start: build_dev  ## Start containers
	$(COMPOSE) up

up: start

up_legacy: build_dev
	$(COMPOSE_LEGACY) up

up_prod: build_prod
	$(COMPOSE_PROD) up

up_prod_detached: build_prod
	$(COMPOSE_PROD) up -d

up_db: build_dev
	$(COMPOSE) up db redis kinto autograph

up_django: build_dev
	$(COMPOSE) up nginx experimenter worker beat db redis kinto autograph

up_detached: build_dev
	$(COMPOSE) up -d

generate_docs: build_dev
	$(COMPOSE) run experimenter sh -c "$(GENERATE_DOCS)"

generate_types: build_dev
	$(COMPOSE) run experimenter sh -c "$(NIMBUS_TYPES_GENERATE)"

format: build_dev  ## Format source tree
	$(COMPOSE) run experimenter sh -c '${PARALLEL} "$(RUFF_FIX);$(DJLINT_FIX);$(BLACK_FIX)" "$(ESLINT_FIX_CORE)" "$(ESLINT_FIX_NIMBUS_UI)" "$(ESLINT_FIX_NIMBUS_UI_NEW)"'
code_format: format

makemigrations: build_dev
	$(COMPOSE) run experimenter python manage.py makemigrations

migrate: build_dev  ## Run database migrations
	$(COMPOSE) run experimenter sh -c "$(WAIT_FOR_DB) $(PYTHON_MIGRATE)"

bash: build_dev
	$(COMPOSE) run experimenter bash

refresh: kill build_dev compose_build  ## Rebuild all containers
	$(COMPOSE) run -e SKIP_DUMMY=$$SKIP_DUMMY experimenter bash -c '$(WAIT_FOR_DB) $(PYTHON_MIGRATE)&&$(LOAD_LOCALES)&&$(LOAD_COUNTRIES)&&$(LOAD_LANGUAGES)&&$(LOAD_FEATURES)&&$(LOAD_DUMMY_EXPERIMENTS)'

dependabot_approve:
	echo "Install and configure the Github CLI https://github.com/cli/cli"
	gh pr list | grep "dependabot/" |  awk '{print $$1}' | xargs -n1 gh pr review -a -b "@dependabot squash and merge"
	gh pr list | grep "dependabot/" |  awk '{print $$1}' | xargs -n1 gh pr merge

# integration tests
integration_shell:
	$(COMPOSE_INTEGRATION) run firefox bash

integration_sdk_shell: build_prod build_integration_test
	$(COMPOSE_INTEGRATION) run rust-sdk bash

integration_vnc_up: build_prod
	$(COMPOSE_INTEGRATION) up firefox

integration_vnc_up_detached: build_prod
	$(COMPOSE_INTEGRATION) up -d firefox

integration_test_legacy: build_prod
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION) run firefox sh -c "./experimenter/tests/experimenter_legacy_tests.sh"

integration_test_nimbus: build_prod
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION) run firefox sh -c "UPDATE_FIREFOX_VERSION=$(UPDATE_FIREFOX_VERSION) FIREFOX_BETA=$(FIREFOX_BETA) PYTEST_SENTRY_DSN=$(PYTEST_SENTRY_DSN) PYTEST_SENTRY_ALWAYS_REPORT=$(PYTEST_SENTRY_ALWAYS_REPORT) CIRCLECI=$(CIRCLECI) ./experimenter/tests/nimbus_integration_tests.sh"

integration_test_nimbus_rust: build_integration_test build_prod
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION) run -it rust-sdk sh -c "./experimenter/tests/nimbus_rust_tests.sh"

integration_test_nimbus_fenix:
	poetry -C experimenter/tests/integration/ -vvv install --no-root
	poetry -C experimenter/tests/integration/ -vvv run pytest --html=experimenter/tests/integration/test-reports/report.htm --self-contained-html --reruns-delay 30 --driver Firefox experimenter/tests/integration/nimbus/android -vvv

# cirrus
CIRRUS_ENABLE = export CIRRUS=1 &&
CIRRUS_BLACK_CHECK = black -l 90 --check --diff .
CIRRUS_BLACK_FIX = black -l 90 .
CIRRUS_RUFF_CHECK = ruff check .
CIRRUS_RUFF_FIX = ruff check --fix .
CIRRUS_PYTEST = pytest . --cov-config=.coveragerc --cov=cirrus
CIRRUS_PYTHON_TYPECHECK = pyright -p .
CIRRUS_PYTHON_TYPECHECK_CREATESTUB = pyright -p . --createstub cirrus
CIRRUS_GENERATE_DOCS = python cirrus/generate_docs.py

cirrus_build: build_megazords
	$(CIRRUS_ENABLE) $(DOCKER_BUILD) --target deploy -f cirrus/server/Dockerfile -t cirrus:deploy cirrus/server/

cirrus_build_test: build_megazords
	$(CIRRUS_ENABLE) $(COMPOSE_TEST) build cirrus

cirrus_bash: cirrus_build
	$(CIRRUS_ENABLE) $(COMPOSE) run cirrus bash

cirrus_up: cirrus_build
	$(CIRRUS_ENABLE) $(COMPOSE) up cirrus

cirrus_down: cirrus_build
	$(CIRRUS_ENABLE) $(COMPOSE) down cirrus

cirrus_test: cirrus_build_test
	$(CIRRUS_ENABLE) $(COMPOSE_TEST) run cirrus sh -c '$(CIRRUS_PYTEST)'

cirrus_check: cirrus_build_test
	$(CIRRUS_ENABLE) $(COMPOSE_TEST) run cirrus sh -c "$(CIRRUS_RUFF_CHECK) && $(CIRRUS_BLACK_CHECK) && $(CIRRUS_PYTHON_TYPECHECK) && $(CIRRUS_PYTEST) && $(CIRRUS_GENERATE_DOCS) --check"

cirrus_code_format: cirrus_build
	$(CIRRUS_ENABLE) $(COMPOSE) run cirrus sh -c '$(CIRRUS_RUFF_FIX) && $(CIRRUS_BLACK_FIX)'

cirrus_typecheck_createstub: cirrus_build
	$(CIRRUS_ENABLE) $(COMPOSE) run cirrus sh -c '$(CIRRUS_PYTHON_TYPECHECK_CREATESTUB)'

cirrus_generate_docs: cirrus_build
	$(CIRRUS_ENABLE) $(COMPOSE) run cirrus sh -c '$(CIRRUS_GENERATE_DOCS)'

build_demo_app:
	$(CIRRUS_ENABLE) $(COMPOSE_INTEGRATION) build demo-app-frontend demo-app-server


# nimbus schemas package
SCHEMAS_ENV ?=  # This is empty by default
SCHEMAS_VERSION = \$$(cat VERSION)
SCHEMAS_RUN = docker run -ti $(SCHEMAS_ENV) -v ./schemas:/schemas -v /schemas/node_modules schemas:dev sh -c
SCHEMAS_BLACK = black --check --diff .
SCHEMAS_RUFF = ruff check .
SCHEMAS_DIFF_PYDANTIC = \
	poetry run python generate_json_schema.py --output /tmp/test_index.d.ts &&\
	diff /tmp/test_index.d.ts index.d.ts || (echo nimbus-schemas typescript package is out of sync please run make schemas_build;exit 1) &&\
	echo 'Done. No problems found in schemas.'
SCHEMAS_TEST = pytest
SCHEMAS_FORMAT = ruff check --fix . && black .
SCHEMAS_DIST_PYPI = poetry build
SCHEMAS_DIST_NPM = poetry run python generate_json_schema.py --output index.d.ts
SCHEMAS_DEPLOY_PYPI = twine upload --skip-existing dist/*;
SCHEMAS_DEPLOY_NPM = echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc;yarn publish --new-version ${SCHEMAS_VERSION} --access public;
SCHEMAS_VERSION_PYPI = poetry version ${SCHEMAS_VERSION};
SCHEMAS_VERSION_NPM = npm version --allow-same-version ${SCHEMAS_VERSION};

schemas_docker_build:  ## Build schemas docker image
	$(DOCKER_BUILD) --target dev -f schemas/Dockerfile -t schemas:dev schemas/

schemas_build: schemas_docker_build schemas_dist  ## Build schemas

schemas_bash: schemas_docker_build
	$(SCHEMAS_RUN) "bash"

schemas_format: schemas_docker_build  ## Format schemas source tree
	$(SCHEMAS_RUN) "$(SCHEMAS_FORMAT)"

schemas_lint: schemas_docker_build  ## Lint schemas source tree
	$(SCHEMAS_RUN) "$(SCHEMAS_BLACK)&&$(SCHEMAS_RUFF)&&$(SCHEMAS_DIFF_PYDANTIC)&&$(SCHEMAS_TEST)"
schemas_check: schemas_lint

schemas_dist_pypi: schemas_docker_build
	$(SCHEMAS_RUN) "$(SCHEMAS_DIST_PYPI)"

schemas_dist_npm: schemas_docker_build schemas_dist_pypi
	$(SCHEMAS_RUN) "$(SCHEMAS_DIST_NPM)"

schemas_dist: schemas_docker_build schemas_dist_pypi schemas_dist_npm

schemas_deploy_pypi: schemas_docker_build
	$(SCHEMAS_RUN) "$(SCHEMAS_DEPLOY_PYPI)"

schemas_deploy_npm: schemas_docker_build
	$(SCHEMAS_RUN) "$(SCHEMAS_DEPLOY_NPM)"

schemas_version_pypi: schemas_docker_build
	$(SCHEMAS_RUN) "$(SCHEMAS_VERSION_PYPI)"

schemas_version_npm: schemas_docker_build
	$(SCHEMAS_RUN) "$(SCHEMAS_VERSION_NPM)"

schemas_version: schemas_version_pypi schemas_version_npm
