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
COMPOSE_FULL = docker-compose -f docker-compose.yml -f docker-compose-full.yml

JOBS = 4
PARALLEL = parallel --halt now,fail=1 --jobs ${JOBS} {} :::
PYTHON_TEST = pytest --cov --cov-report term-missing
PYTHON_CHECK_MIGRATIONS = python manage.py makemigrations --check --dry-run --noinput
ESLINT = yarn workspace @experimenter/core lint
ESLINT_FIX = yarn workspace @experimenter/core lint-fix
JS_TEST = yarn workspace @experimenter/core test
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

test: test_build
	$(COMPOSE_TEST) run app sh -c '$(WAIT_FOR_DB) ${PARALLEL} "$(PYTHON_TEST)" "$(JS_TEST)"'

eslint: test_build
	$(COMPOSE_TEST) run app sh -c "$(ESLINT)"

py_test: test_build
	$(COMPOSE_TEST) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_TEST)"

js_test: test_build
	$(COMPOSE_TEST) run app sh -c "$(JS_TEST)"

flake8: test_build
	$(COMPOSE_TEST) run app sh -c "$(FLAKE8)"

black_check: test_build
	$(COMPOSE_TEST) run app sh -c "$(BLACK_CHECK)"

check_migrations: test_build
	$(COMPOSE_TEST) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_CHECK_MIGRATIONS)"

check_docs: test_build
	$(COMPOSE_TEST) run app sh -c "$(CHECK_DOCS)"

check: test_build
	$(COMPOSE_TEST) run app sh -c '$(WAIT_FOR_DB) ${PARALLEL} "$(PYTHON_CHECK_MIGRATIONS)" "$(CHECK_DOCS)" "$(BLACK_CHECK)" "$(FLAKE8)" "$(ESLINT)" "$(PYTHON_TEST)" "$(JS_TEST)"'

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

up_detached: compose_stop compose_build
	$(COMPOSE) up -d

generate_docs: compose_build
	$(COMPOSE) run app sh -c "$(GENERATE_DOCS)"

eslint_fix: test_build
	$(COMPOSE) run app sh -c "$(ESLINT_FIX)"

black_fix: test_build
	$(COMPOSE) run app sh -c "$(BLACK_FIX)"

code_format: compose_build
	$(COMPOSE) run app sh -c "$(BLACK_FIX)&&$(ESLINT_FIX)"

makemigrations: compose_build
	$(COMPOSE) run app python manage.py makemigrations

migrate: compose_build
	$(COMPOSE) run app sh -c "$(WAIT_FOR_DB) python manage.py migrate"

createuser: compose_build
	$(COMPOSE) run app python manage.py createsuperuser

load_locales_countries: compose_build
	$(COMPOSE) run app sh -c "$(WAIT_FOR_DB) $(LOAD_LOCALES)&&$(LOAD_COUNTRIES)"

load_dummy_experiments: compose_build
	$(COMPOSE) run app python manage.py load_dummy_experiments

shell: compose_build
	$(COMPOSE) run app python manage.py shell

dbshell: compose_build
	$(COMPOSE) run app python manage.py dbshell

bash: compose_build
	$(COMPOSE) run app bash

refresh: kill compose_build
	$(COMPOSE) run app sh -c '$(WAIT_FOR_DB) $(MIGRATE)&&$(LOAD_LOCALES)&&$(LOAD_COUNTRIES)&&$(LOAD_DUMMY_EXPERIMENTS)'

# experimenter + delivery console + normandy stack
compose_build_all: build ssl
	 $(COMPOSE_FULL) build

up_all: compose_build_all
	$(COMPOSE_FULL) up

kill_all: kill
	$(COMPOSE_FULL) kill
	$(COMPOSE_FULL) -v rm

normandy_shell: compose_build_all
	$(COMPOSE_FULL) run normandy ./manage.py shell

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