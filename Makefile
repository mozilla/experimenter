ssl: nginx/key.pem nginx/cert.pem

nginx/key.pem:
	openssl genrsa -out nginx/key.pem 4096

nginx/cert.pem: nginx/key.pem
	openssl req -new -x509 -nodes -sha256 -key nginx/key.pem \
		-subj "/C=US/ST=California/L=Mountain View/O=Mozilla/CN=experiment_local" \
		> nginx/cert.pem

secretkey:
	openssl rand -hex 24

build:
	./scripts/build.sh

WAIT_FOR_DB = /app/bin/wait-for-it.sh db:5432 &&

COMPOSE = docker-compose -f docker-compose.yml
COMPOSE_TEST = docker-compose -f docker-compose-test.yml
COMPOSE_INTEGRATION = docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml

JOBS = 4
PARALLEL = parallel --halt now,fail=1 --jobs ${JOBS} {} :::
PY_IMPORT_SORT =  python -m isort . -m VERTICAL_HANGING_INDENT --tc
PY_IMPORT_CHECK =  python -m isort . -m VERTICAL_HANGING_INDENT --tc --check
PYTHON_TEST = pytest --cov --cov-report term-missing
PYTHON_CHECK_MIGRATIONS = python manage.py makemigrations --check --dry-run --noinput
ESLINT_CORE = yarn workspace @experimenter/core lint
ESLINT_FIX_CORE = yarn workspace @experimenter/core lint-fix
ESLINT_RAPID = yarn workspace @experimenter/rapid lint:eslint
ESLINT_VISUALIZATION = yarn workspace @experimenter/visualization lint
ESLINT_FIX_RAPID = yarn workspace @experimenter/rapid lint:eslint --fix
TYPECHECK_RAPID = yarn workspace @experimenter/rapid lint:tsc
JS_TEST_CORE = yarn workspace @experimenter/core test
JS_TEST_RAPID = yarn workspace @experimenter/rapid test
FLAKE8 = flake8 .
BLACK_CHECK = black -l 90 --check --diff .
BLACK_FIX = black -l 90 .
CHECK_DOCS = python manage.py generate_docs --check=true
GENERATE_DOCS = python manage.py generate_docs
LOAD_COUNTRIES = python manage.py loaddata ./experimenter/base/fixtures/countries.json
LOAD_LOCALES = python manage.py loaddata ./experimenter/base/fixtures/locales.json
LOAD_DUMMY_EXPERIMENTS = python manage.py load_dummy_experiments
MIGRATE = python manage.py migrate

test_build: build
	$(COMPOSE_TEST) build

check: test_build
	$(COMPOSE_TEST) run app sh -c '$(WAIT_FOR_DB) ${PARALLEL} "$(PYTHON_CHECK_MIGRATIONS)" "$(CHECK_DOCS)" "${PY_IMPORT_CHECK}"  "$(BLACK_CHECK)" "$(FLAKE8)" "$(ESLINT_CORE)" "$(ESLINT_RAPID)" "$(ESLINT_VISUALIZATION)" "$(TYPECHECK_RAPID)" "$(PYTHON_TEST)" "$(JS_TEST_CORE)" "$(JS_TEST_RAPID)"'

compose_build: build ssl
	$(COMPOSE)  build

compose_stop:
	$(COMPOSE) kill
	$(COMPOSE_INTEGRATION) kill

compose_rm:
	$(COMPOSE) rm -f -v
	$(COMPOSE_INTEGRATION) rm -f -v

volumes_rm:
	docker volume ls -q | xargs docker volume rm -f | echo

kill: compose_stop compose_rm volumes_rm
	echo "All containers removed!"

up: compose_stop compose_build
	$(COMPOSE) up

up_db: compose_stop compose_build
	$(COMPOSE) up db redis kinto autograph

up_django: compose_stop compose_build
	$(COMPOSE) up nginx app worker beat db redis kinto autograph

up_detached: compose_stop compose_build
	$(COMPOSE) up -d

generate_docs: compose_build
	$(COMPOSE) run app sh -c "$(GENERATE_DOCS)"

code_format: compose_build
	$(COMPOSE) run app sh -c "${PY_IMPORT_SORT}&&$(BLACK_FIX)&&$(ESLINT_FIX_CORE)&&$(ESLINT_FIX_RAPID)"

makemigrations: compose_build
	$(COMPOSE) run app python manage.py makemigrations

migrate: compose_build
	$(COMPOSE) run app sh -c "$(WAIT_FOR_DB) python manage.py migrate"

load_locales_countries: compose_build
	$(COMPOSE) run app sh -c "$(WAIT_FOR_DB) $(LOAD_LOCALES)&&$(LOAD_COUNTRIES)"

load_dummy_experiments: compose_build
	$(COMPOSE) run app python manage.py load_dummy_experiments

bash: compose_build
	$(COMPOSE) run app bash

refresh: kill compose_build
	$(COMPOSE) run app sh -c '$(WAIT_FOR_DB) $(MIGRATE)&&$(LOAD_LOCALES)&&$(LOAD_COUNTRIES)&&$(LOAD_DUMMY_EXPERIMENTS)'

# integration tests
integration_build: compose_build
	$(COMPOSE_INTEGRATION) build

integration_shell: integration_build
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION) run firefox bash

integration_vnc_up: integration_build
	$(COMPOSE_INTEGRATION) up firefox

integration_vnc_up_shell: integration_build
	$(COMPOSE_INTEGRATION) run firefox bash

integration_vnc_up_detached: integration_build
	$(COMPOSE_INTEGRATION) up -d firefox

integration_test: integration_build
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION) run firefox tox -c app/tests/integration -- -n 4