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

WAIT_FOR_DB = /app/bin/wait-for-it.sh db:5432 --

COMPOSE = docker-compose -f docker-compose.yml
COMPOSE_TEST = docker-compose -f docker-compose-test.yml
COMPOSE_INTEGRATION = docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml
COMPOSE_FULL = docker-compose -f docker-compose.yml -f docker-compose-full.yml

PYTHON_TEST = pytest -vvvv --cov --cov-report term-missing --show-capture=no
PYTHON_TEST_FAST = python manage.py test -v 3 --parallel
PYTHON_CHECK_MIGRATIONS = python manage.py makemigrations --check --dry-run --noinput
ESLINT = yarn lint
ESLINT_FIX = yarn lint-fix
JS_TEST = yarn test
FLAKE8 = flake8 .
BLACK_CHECK = black -l 90 --check .
BLACK_FIX = black -l 90 .
CHECK_DOCS = python manage.py generate-docs --check=true
GENERATE_DOCS = python manage.py generate-docs

test_build: build
	$(COMPOSE_TEST) build

test: test_build
	$(COMPOSE_TEST) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_TEST)&&$(JS_TEST)"

testfast: test_build
	$(COMPOSE_TEST) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_TEST_FAST)"

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
	$(COMPOSE_TEST) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_CHECK_MIGRATIONS)&&$(CHECK_DOCS)&&$(BLACK_CHECK)&&$(FLAKE8)&&$(ESLINT)&&$(PYTHON_TEST)&&$(JS_TEST)"

checkfast: test_build
	$(COMPOSE_TEST) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_CHECK_MIGRATIONS)&&$(BLACK_CHECK)&&$(FLAKE8)&&$(ESLINT)&&$(PYTHON_TEST_FAST)"

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

load_locales: compose_build
	$(COMPOSE) run app python manage.py loaddata ./fixtures/locales.json

load_countries: compose_build
	$(COMPOSE) run app python manage.py load-countries

load_locales_countries:load_locales load_countries

load_dummy_experiments: compose_build
	$(COMPOSE) run app python manage.py load-dummy-experiments

shell: compose_build
	$(COMPOSE) run app python manage.py shell

dbshell: compose_build
	$(COMPOSE) run app python manage.py dbshell

bash: compose_build
	$(COMPOSE) run app bash

refresh: kill migrate load_locales_countries load_dummy_experiments

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
	$(COMPOSE_INTEGRATION) run firefox bash

integration_vnc_up: integration_build
	$(COMPOSE_INTEGRATION) up vnc

integration_vnc_up_detached: integration_build
	$(COMPOSE_INTEGRATION) up vnc -d

integration_test: integration_build
	$(COMPOSE_INTEGRATION) run firefox tox -c tests/integration