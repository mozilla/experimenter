WAIT_FOR_DB = /app/bin/wait-for-it.sh -t 30 db:5432 &&
WAIT_FOR_RUNSERVER = /app/bin/wait-for-it.sh -t 30 localhost:7001 &&

COMPOSE = docker-compose -f docker-compose.yml
COMPOSE_TEST = docker-compose -f docker-compose-test.yml
COMPOSE_PROD = docker-compose -f docker-compose-prod.yml
COMPOSE_INTEGRATION = ${COMPOSE_PROD} -f docker-compose-integration-test.yml

JOBS = 4
PARALLEL = parallel --halt now,fail=1 --jobs ${JOBS} {} :::
NOCOLOR= \033[0m
RED = \033[0;31m
GREEN = \033[0;32m
PAD = -------------------------------------------------\n
COLOR_CHECK = && echo "${GREEN}${PAD}All Checks Passed\n${PAD}${NOCOLOR}" || (echo "${RED}${PAD}Some Checks Failed\n${PAD}${NOCOLOR}";exit 1)
PY_IMPORT_SORT =  python -m isort . --profile black
PY_IMPORT_CHECK =  python -m isort . --profile black --check
PYTHON_TEST = pytest --cov --cov-report term-missing
PYTHON_CHECK_MIGRATIONS = python manage.py makemigrations --check --dry-run --noinput
PYTHON_MIGRATE = python manage.py migrate
ESLINT_CORE = yarn workspace @experimenter/core lint
ESLINT_FIX_CORE = yarn workspace @experimenter/core lint-fix
ESLINT_NIMBUS_UI = yarn workspace @experimenter/nimbus-ui lint
ESLINT_FIX_NIMBUS_UI = yarn workspace @experimenter/nimbus-ui lint-fix
TYPECHECK_NIMBUS_UI = yarn workspace @experimenter/nimbus-ui lint:tsc
JS_TEST_CORE = yarn workspace @experimenter/core test
JS_TEST_NIMBUS_UI = CI=yes yarn workspace @experimenter/nimbus-ui test:cov
NIMBUS_SCHEMA_CHECK = python manage.py graphql_schema --out experimenter/nimbus-ui/test_schema.graphql&&diff experimenter/nimbus-ui/test_schema.graphql experimenter/nimbus-ui/schema.graphql || (echo GraphQL Schema is out of sync please run make generate_types;exit 1)
NIMBUS_TYPES_GENERATE = python manage.py graphql_schema --out experimenter/nimbus-ui/schema.graphql&&yarn workspace @experimenter/nimbus-ui generate-types
FLAKE8 = flake8 .
BLACK_CHECK = black -l 90 --check --diff . --exclude node_modules
BLACK_FIX = black -l 90 . --exclude node_modules
CHECK_DOCS = python manage.py generate_docs --check=true
GENERATE_DOCS = python manage.py generate_docs
LOAD_COUNTRIES = python manage.py loaddata ./experimenter/base/fixtures/countries.json
LOAD_LOCALES = python manage.py loaddata ./experimenter/base/fixtures/locales.json
LOAD_DUMMY_EXPERIMENTS = python manage.py load_dummy_experiments
PUBLISH_STORYBOOKS = npx github:mozilla-fxa/storybook-gcp-publisher --commit-summary commit-summary.txt --commit-description commit-description.txt --version-json version.json

ssl: nginx/key.pem nginx/cert.pem

nginx/key.pem:
	openssl genrsa -out nginx/key.pem 4096

nginx/cert.pem: nginx/key.pem
	openssl req -new -x509 -nodes -sha256 -key nginx/key.pem \
		-subj "/C=US/ST=California/L=Mountain View/O=Mozilla/CN=experiment_local" \
		> nginx/cert.pem

secretkey:
	openssl rand -hex 24

build_dev:
	docker build --target dev -f app/Dockerfile -t app:dev app/

build_test:
	docker build --target test -f app/Dockerfile -t app:test app/

build_prod:
	docker build --target deploy -f app/Dockerfile -t app:deploy app/

test_build: build_test
	$(COMPOSE_TEST) build

check: test_build
	$(COMPOSE_TEST) run app sh -c '$(WAIT_FOR_DB) (${PARALLEL} "$(NIMBUS_SCHEMA_CHECK)" "$(PYTHON_CHECK_MIGRATIONS)" "$(CHECK_DOCS)" "${PY_IMPORT_CHECK}"  "$(BLACK_CHECK)" "$(FLAKE8)" "$(ESLINT_CORE)" "$(ESLINT_NIMBUS_UI)" "$(TYPECHECK_NIMBUS_UI)" "$(JS_TEST_CORE)" "$(JS_TEST_NIMBUS_UI)" "$(PYTHON_TEST)") ${COLOR_CHECK}'

py_test: test_build
	$(COMPOSE_TEST) run app sh -c '$(WAIT_FOR_DB) $(PYTHON_TEST)'

compose_build: build_dev ssl
	$(COMPOSE)  build

compose_stop:
	$(COMPOSE) kill
	$(COMPOSE_INTEGRATION) kill
	$(COMPOSE_PROD) kill

compose_rm:
	$(COMPOSE) rm -f -v
	$(COMPOSE_INTEGRATION) rm -f -v
	$(COMPOSE_PROD) rm -f -v

volumes_rm:
	docker volume prune -f

static_rm:
	rm -Rf app/node_modules
	rm -Rf app/experimenter/legacy-ui/core/node_modules/
	rm -Rf app/experimenter/nimbus-ui/node_modules/
	rm -Rf app/experimenter/legacy-ui/assets/
	rm -Rf app/experimenter/nimbus-ui/build/

kill: compose_stop compose_rm volumes_rm
	echo "All containers removed!"

up: compose_build
	$(COMPOSE) up

up_prod: compose_build build_prod
	$(COMPOSE_PROD) up

up_prod_detached: compose_build build_prod
	$(COMPOSE_PROD) up -d

up_db: compose_build
	$(COMPOSE) up db redis kinto autograph

up_django: compose_build
	$(COMPOSE) up nginx app worker beat db redis kinto autograph

up_detached: compose_build
	$(COMPOSE) up -d

generate_docs: compose_build
	$(COMPOSE) run app sh -c "$(GENERATE_DOCS)"

generate_types: build_dev
	$(COMPOSE) run app sh -c "$(NIMBUS_TYPES_GENERATE)"

publish_storybooks: build_test
	$(COMPOSE_TEST) run app sh -c "$(PUBLISH_STORYBOOKS)"

code_format: compose_build
	$(COMPOSE) run app sh -c '${PARALLEL} "${PY_IMPORT_SORT};$(BLACK_FIX)" "$(ESLINT_FIX_CORE)" "$(ESLINT_FIX_NIMBUS_UI)"'

makemigrations: compose_build
	$(COMPOSE) run app python manage.py makemigrations

migrate: compose_build
	$(COMPOSE) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_MIGRATE)"

bash: compose_build
	$(COMPOSE) run app bash

refresh: kill compose_build
	$(COMPOSE) run app sh -c '$(WAIT_FOR_DB) $(PYTHON_MIGRATE)&&$(LOAD_LOCALES)&&$(LOAD_COUNTRIES)&&$(LOAD_DUMMY_EXPERIMENTS)'

# integration tests
integration_build: build_prod ssl
	$(COMPOSE_INTEGRATION) build

integration_shell: integration_build
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION) run firefox bash

integration_vnc_up: integration_build
	$(COMPOSE_INTEGRATION) up firefox

integration_vnc_up_detached: integration_build
	$(COMPOSE_INTEGRATION) up -d firefox

integration_test: integration_build
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION) run firefox sh -c "sudo chmod a+rwx /code/app/tests/integration/.tox;tox -c app/tests/integration -- -n 4"
