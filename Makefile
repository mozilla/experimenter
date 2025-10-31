SHELL = /usr/bin/env bash

WAIT_FOR_DB = /experimenter/bin/wait-for-it.sh -t 30 db:5432 &&
WAIT_FOR_RUNSERVER = /experimenter/bin/wait-for-it.sh -t 30 localhost:7001 &&

COMPOSE_CIRRUS = [[ -n $$CIRRUS ]] && echo "-f docker-compose-cirrus.yml"
COMPOSE = docker compose -f docker-compose.yml $$(${COMPOSE_CIRRUS})
COMPOSE_RUN = ${COMPOSE} run --rm
COMPOSE_LEGACY = ${COMPOSE} -f docker-compose-legacy.yml
COMPOSE_TEST = docker compose -f docker-compose-test.yml
COMPOSE_TEST_RUN = ${COMPOSE_TEST} run --name experimenter_test
COMPOSE_PROD = docker compose -f docker-compose-prod.yml $$(${COMPOSE_CIRRUS})
COMPOSE_INTEGRATION = ${COMPOSE_PROD} -f docker-compose-integration-test.yml $$(${COMPOSE_CIRRUS})
COMPOSE_INTEGRATION_RUN = ${COMPOSE_INTEGRATION} run --name experimenter_integration
DOCKER_BUILD = docker buildx build

WORKFLOW := build
EPOCH_TIME := $(shell date +"%s")
TEST_RESULTS_DIR ?= $(if $(CIRCLECI),dashboard/test-results,.)
TEST_FILE_PREFIX := $(if $(CIRCLECI),$(CIRCLE_BUILD_NUM)__$(EPOCH_TIME)__$(CIRCLE_PROJECT_REPONAME)__$(WORKFLOW)__)
UNIT_JUNIT_XML := $(TEST_RESULTS_DIR)/$(TEST_FILE_PREFIX)unit__results.xml
UNIT_COVERAGE_JSON := $(TEST_RESULTS_DIR)/$(TEST_FILE_PREFIX)unit__coverage.json
UI_COVERAGE_JSON := $(TEST_RESULTS_DIR)/$(TEST_FILE_PREFIX)ui__coverage.json
UI_JUNIT_XML := $(TEST_RESULTS_DIR)/$(TEST_FILE_PREFIX)ui__results.xml
INTEGRATION_JUNIT_XML := $(TEST_RESULTS_DIR)/$(TEST_FILE_PREFIX)integration__results.xml

JOBS = 4
PARALLEL = parallel --halt now,fail=1 --jobs ${JOBS} {} :::
NOCOLOR= \033[0m
RED = \033[0;31m
GREEN = \033[0;32m
PAD = -------------------------------------------------\n
COLOR_CHECK = && echo "${GREEN}${PAD}All Checks Passed\n${PAD}${NOCOLOR}" || (echo "${RED}${PAD}Some Checks Failed\n${PAD}${NOCOLOR}";exit 1)
PYTHON_COVERAGE = pytest --cov --cov-report json:experimenter_coverage.json --cov-branch --junitxml=experimenter_tests.xml
PYTHON_TEST = pytest --cov --cov-report term-missing
PYTHON_TYPECHECK = pyright experimenter/
PYTHON_CHECK_MIGRATIONS = python manage.py makemigrations --check --dry-run --noinput
PYTHON_MIGRATE = python manage.py migrate
ESLINT_LEGACY = yarn workspace @experimenter/core lint
ESLINT_FIX_CORE = yarn workspace @experimenter/core lint-fix
ESLINT_RESULTS = yarn workspace @experimenter/results lint
ESLINT_FIX_RESULTS = yarn workspace @experimenter/results lint-fix
ESLINT_NIMBUS_UI = yarn workspace @experimenter/nimbus_ui lint
ESLINT_FIX_NIMBUS_UI = yarn workspace @experimenter/nimbus_ui format
TYPECHECK_RESULTS = yarn workspace @experimenter/results lint:tsc
DJLINT_CHECK = djlint --check experimenter/nimbus_ui/ experimenter/glean/
DJLINT_FIX = djlint --reformat experimenter/nimbus_ui/ experimenter/glean/
JS_TEST_LEGACY = yarn workspace @experimenter/core test
JS_TEST_RESULTS = DEBUG_PRINT_LIMIT=999999 CI=yes yarn workspace @experimenter/results test:cov
RESULTS_SCHEMA_CHECK = python manage.py graphql_schema --out experimenter/results/test_schema.graphql&&diff experimenter/results/test_schema.graphql experimenter/results/schema.graphql || (echo GraphQL Schema is out of sync please run make generate_types;exit 1)
RESULTS_TYPES_GENERATE = python manage.py graphql_schema --out experimenter/results/schema.graphql&&yarn workspace @experimenter/results generate-types
RUFF_CHECK = ruff check experimenter/ manifesttool/ tests/
RUFF_FIX = ruff check --fix experimenter/ manifesttool/ tests/
RUFF_FORMAT_CHECK = ruff format --check --diff .
RUFF_FORMAT_FIX = ruff format .
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
	$(COMPOSE_RUN) --no-deps -e GITHUB_BEARER_TOKEN=$(GITHUB_BEARER_TOKEN) experimenter /experimenter/bin/manifest-tool.py fetch $(FETCH_ARGS)

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
	-docker rm experimenter_test
	$(COMPOSE_TEST_RUN) experimenter sh -c '$(WAIT_FOR_DB) (${PARALLEL} "$(PYTHON_CHECK_MIGRATIONS)" "$(CHECK_DOCS)" "$(RUFF_FORMAT_CHECK)" "$(RUFF_CHECK)" "$(DJLINT_CHECK)" "$(ESLINT_LEGACY)" "$(ESLINT_RESULTS)" "$(ESLINT_NIMBUS_UI)" "$(PYTHON_TYPECHECK)" "$(PYTHON_TEST)" "$(JS_TEST_LEGACY)" "$(JS_TEST_RESULTS)" "$(RESULTS_SCHEMA_CHECK)") ${COLOR_CHECK}'

check: lint

check_and_report: build_test  ## Only to be used on CI
	-docker rm experimenter_test
	$(COMPOSE_TEST_RUN) experimenter sh -c '$(WAIT_FOR_DB) (${PARALLEL} "$(PYTHON_COVERAGE)") ${COLOR_CHECK}' || true
	docker cp experimenter_test:/experimenter/experimenter_coverage.json workspace/test-results
	docker cp experimenter_test:/experimenter/experimenter_tests.xml workspace/test-results
	cp workspace/test-results/experimenter_coverage.json $(UNIT_COVERAGE_JSON)
	cp workspace/test-results/experimenter_tests.xml $(UNIT_JUNIT_XML)

test: build_test  ## Run tests
	-docker rm experimenter_test
	$(COMPOSE_TEST_RUN) experimenter sh -c '$(WAIT_FOR_DB) python manage.py test --parallel'
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
	$(COMPOSE_RUN) experimenter sh -c "$(GENERATE_DOCS)"

generate_types: build_dev
	$(COMPOSE_RUN) experimenter sh -c "$(RESULTS_TYPES_GENERATE)"

format: build_dev  ## Format source tree
	$(COMPOSE_RUN) experimenter sh -c '${PARALLEL} "$(RUFF_FIX);$(DJLINT_FIX);$(RUFF_FORMAT_FIX)" "$(ESLINT_FIX_CORE)" "$(ESLINT_FIX_RESULTS)" "$(ESLINT_FIX_NIMBUS_UI)"'
code_format: format

makemigrations: build_dev
	$(COMPOSE_RUN) experimenter python manage.py makemigrations

migrate: build_dev  ## Run database migrations
	$(COMPOSE_RUN) experimenter sh -c "$(WAIT_FOR_DB) $(PYTHON_MIGRATE)"

bash: build_dev
	$(COMPOSE_RUN) experimenter bash

refresh: kill build_dev compose_build refresh_db  ## Rebuild all containers and the database

refresh_db:  # Rebuild the database
	$(COMPOSE_RUN) -e SKIP_DUMMY=$$SKIP_DUMMY experimenter bash -c '$(WAIT_FOR_DB) $(PYTHON_MIGRATE)&&$(LOAD_LOCALES)&&$(LOAD_COUNTRIES)&&$(LOAD_LANGUAGES)&&$(LOAD_FEATURES)&&$(LOAD_DUMMY_EXPERIMENTS)'

dependabot_approve:
	echo "Install and configure the Github CLI https://github.com/cli/cli"
	gh pr list | grep "dependabot/" |  awk '{print $$1}' | xargs -n1 gh pr review -a -b "@dependabot squash and merge"
	gh pr list | grep "dependabot/" |  awk '{print $$1}' | xargs -n1 gh pr merge

# integration tests
integration_shell:
	$(COMPOSE_INTEGRATION_RUN) firefox bash

integration_clean:
	-docker rm experimenter_integration

integration_sdk_shell: build_prod build_integration_test
	$(COMPOSE_INTEGRATION_RUN) rust-sdk bash

integration_vnc_shell: build_prod
	$(COMPOSE_INTEGRATION) up -d firefox
	docker exec -it $$(docker ps -qf "name=experimenter-firefox-1") bash

integration_test_legacy: build_prod integration_clean
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION_RUN) firefox sh -c "./experimenter/tests/experimenter_legacy_tests.sh"

integration_test_nimbus_desktop: build_prod integration_clean
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION_RUN) firefox sh -c "FIREFOX_CHANNEL=$(FIREFOX_CHANNEL) PYTEST_SENTRY_DSN=$(PYTEST_SENTRY_DSN) PYTEST_SENTRY_ALWAYS_REPORT=$(PYTEST_SENTRY_ALWAYS_REPORT) CIRCLECI=$(CIRCLECI) ./experimenter/tests/nimbus_integration_tests.sh"

integration_test_nimbus_sdk: build_integration_test build_prod
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION_RUN) -it rust-sdk sh -c "./experimenter/tests/nimbus_rust_tests.sh"

integration_test_nimbus_fenix:
	poetry -C experimenter/tests/integration/ -vvv install --no-root
	poetry -C experimenter/tests/integration/ -vvv run pytest --html=workspace/test-results/report.htm --self-contained-html --reruns-delay 30 --driver Firefox experimenter/tests/integration/nimbus/android --junitxml=experimenter/tests/integration/test-reports/experimenter_fenix_integration_tests.xml -vvv
	cp experimenter/tests/integration/test-reports/experimenter_fenix_integration_tests.xml $(TEST_RESULTS_DIR)/$(TEST_FILE_PREFIX)integration__results.xml

make integration_test_and_report:
	docker cp experimenter_integration:/code/experimenter/tests/integration/test-reports/experimenter_integration_tests.xml workspace/test-results
	cp workspace/test-results/experimenter_integration_tests.xml $(INTEGRATION_JUNIT_XML)

# cirrus
CIRRUS_ENABLE = export CIRRUS=1 &&
CIRRUS_BLACK_CHECK = black -l 90 --check --diff .
CIRRUS_BLACK_FIX = black -l 90 .
CIRRUS_RUFF_CHECK = ruff check .
CIRRUS_RUFF_FIX = ruff check --fix .
CIRRUS_PYTEST = pytest . --cov-config=.coveragerc --cov=cirrus --cov-branch --cov-report json:cirrus_coverage.json --junitxml=cirrus_pytest.xml -v
CIRRUS_PYTHON_TYPECHECK = pyright -p .
CIRRUS_PYTHON_TYPECHECK_CREATESTUB = pyright -p . --createstub cirrus
CIRRUS_GENERATE_DOCS = python cirrus/generate_docs.py
CIRRUS_COVERAGE_JSON := $(TEST_RESULTS_DIR)/$(TEST_FILE_PREFIX)unit__coverage.json
CIRRUS_JUNIT_XML := $(TEST_RESULTS_DIR)/$(TEST_FILE_PREFIX)integration__results.xml

cirrus_build: build_megazords
	$(CIRRUS_ENABLE) $(DOCKER_BUILD) --target deploy -f cirrus/server/Dockerfile -t cirrus:deploy --build-context=fml=experimenter/experimenter/features/manifests/ cirrus/server/

cirrus_build_dev: build_megazords
	$(CIRRUS_ENABLE) $(DOCKER_BUILD) --target dev -f cirrus/server/Dockerfile -t cirrus:dev --build-context=fml=experimenter/experimenter/features/manifests/ cirrus/server/

cirrus_build_test: build_megazords
	$(CIRRUS_ENABLE) $(COMPOSE_TEST) build cirrus

cirrus_bash: cirrus_build_dev
	docker run --rm -ti -v ./cirrus/server:/cirrus cirrus:dev bash

cirrus_up: cirrus_build
	$(CIRRUS_ENABLE) $(COMPOSE) up cirrus

cirrus_down: cirrus_build
	$(CIRRUS_ENABLE) $(COMPOSE) down cirrus

cirrus_test: cirrus_build_test
	-docker rm experimenter_test
	$(CIRRUS_ENABLE) $(COMPOSE_TEST_RUN) cirrus sh -c '$(CIRRUS_PYTEST)'

cirrus_check: cirrus_lint

cirrus_lint: cirrus_build_test integration_clean
	-docker rm experimenter_test
	$(CIRRUS_ENABLE) $(COMPOSE_TEST_RUN) cirrus sh -c "$(CIRRUS_RUFF_CHECK) && $(CIRRUS_BLACK_CHECK) && $(CIRRUS_PYTHON_TYPECHECK) && $(CIRRUS_PYTEST) && $(CIRRUS_GENERATE_DOCS) --check"

cirrus_check_and_report: cirrus_lint
	docker cp experimenter_test:/cirrus/cirrus_pytest.xml workspace/test-results
	docker cp experimenter_test:/cirrus/cirrus_coverage.json workspace/test-results
	cp workspace/test-results/cirrus_pytest.xml $(CIRRUS_JUNIT_XML)
	cp workspace/test-results/cirrus_coverage.json $(CIRRUS_COVERAGE_JSON)

cirrus_code_format: cirrus_build
	$(CIRRUS_ENABLE) $(COMPOSE_RUN) cirrus sh -c '$(CIRRUS_RUFF_FIX) && $(CIRRUS_BLACK_FIX)'

cirrus_typecheck_createstub: cirrus_build
	$(CIRRUS_ENABLE) $(COMPOSE_RUN) cirrus sh -c '$(CIRRUS_PYTHON_TYPECHECK_CREATESTUB)'

cirrus_generate_docs: cirrus_build
	$(CIRRUS_ENABLE) $(COMPOSE_RUN) cirrus sh -c '$(CIRRUS_GENERATE_DOCS)'

build_demo_app:
	$(CIRRUS_ENABLE) $(COMPOSE_INTEGRATION) build demo-app-frontend demo-app-server


# nimbus schemas package
SCHEMAS_ENV ?=  # This is empty by default
SCHEMAS_VERSION = \$$(cat VERSION)
SCHEMAS_RUN = docker run --rm -ti $(SCHEMAS_ENV) -v ./schemas:/schemas -v /schemas/node_modules schemas:dev sh -c
SCHEMAS_BLACK = black --check --diff .
SCHEMAS_RUFF = ruff check .
SCHEMAS_DIFF_PYDANTIC = \
	poetry run python generate_json_schema.py --output /tmp/test_index.d.ts &&\
	diff /tmp/test_index.d.ts index.d.ts || (echo nimbus-schemas typescript package is out of sync please run make schemas_build;exit 1) &&\
	echo 'Done. No problems found in schemas.'
SCHEMAS_TEST = pytest
SCHEMAS_FORMAT = ruff check --fix . && black .
SCHEMAS_GENERATE = poetry run python generate_json_schema.py
SCHEMAS_DIST_PYPI = poetry build
SCHEMAS_DEPLOY_PYPI = twine upload --skip-existing dist/*;
SCHEMAS_DEPLOY_NPM = echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc;yarn publish --new-version ${SCHEMAS_VERSION} --access public;
SCHEMAS_VERSION_PYPI = poetry version ${SCHEMAS_VERSION};
SCHEMAS_VERSION_NPM = npm version --allow-same-version ${SCHEMAS_VERSION};

schemas_docker_build:  ## Build schemas docker image
	$(DOCKER_BUILD) --target dev -f schemas/Dockerfile -t schemas:dev schemas/

schemas_build: schemas_docker_build  ## Build the mozilla_nimbus_schemas packages.
	$(SCHEMAS_RUN) "$(SCHEMAS_GENERATE) && $(SCHEMAS_DIST_PYPI)"

schemas_bash: schemas_docker_build
	$(SCHEMAS_RUN) "bash"

schemas_format: schemas_docker_build  ## Format schemas source tree
	$(SCHEMAS_RUN) "$(SCHEMAS_FORMAT)"

schemas_lint: schemas_docker_build  ## Lint schemas source tree
	$(SCHEMAS_RUN) "$(SCHEMAS_BLACK)&&$(SCHEMAS_RUFF)&&$(SCHEMAS_DIFF_PYDANTIC)&&$(SCHEMAS_TEST)"

schemas_check: schemas_lint

schemas_generate: schemas_docker_build
	$(SCHEMAS_RUN) "$(SCHEMAS_GENERATE)"


schemas_deploy_pypi: schemas_build
	$(SCHEMAS_RUN) "$(SCHEMAS_DEPLOY_PYPI)"

schemas_deploy_npm: schemas_build
	$(SCHEMAS_RUN) "$(SCHEMAS_DEPLOY_NPM)"

schemas_version_pypi: schemas_docker_build
	$(SCHEMAS_RUN) "$(SCHEMAS_VERSION_PYPI)"

schemas_version_npm: schemas_docker_build
	$(SCHEMAS_RUN) "$(SCHEMAS_VERSION_NPM)"

schemas_version: schemas_version_pypi schemas_version_npm
