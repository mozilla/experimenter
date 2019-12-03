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

PYTHON_TEST = pytest -vvvv --cov --cov-report term-missing --show-capture=no
PYTHON_TEST_FAST = python manage.py test -v 3 --parallel
PYTHON_CHECK_MIGRATIONS = python manage.py makemigrations --check --dry-run --noinput
ESLINT = yarn lint
ESLINT_FIX = yarn lint-fix
FLAKE8 = flake8 .
BLACK_CHECK = black -l 90 --check .
BLACK_FIX = black -l 90 .

test_build: build
	$(COMPOSE_TEST) build

test: test_build
	$(COMPOSE_TEST) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_TEST)"

testfast: test_build
	$(COMPOSE_TEST) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_TEST_FAST)"

eslint: test_build
	$(COMPOSE_TEST) run app sh -c "$(ESLINT)"

eslint_fix: test_build
	$(COMPOSE_TEST) run app sh -c "$(ESLINT_FIX)"

flake8: test_build
	$(COMPOSE_TEST) run app sh -c "$(FLAKE8)"

black_check: test_build
	$(COMPOSE_TEST) run app sh -c "$(BLACK_CHECK)"

black_fix: test_build
	$(COMPOSE_TEST) run app sh -c "$(BLACK_FIX)"

code_format: test_build
	$(COMPOSE_TEST) run app sh -c "$(BLACK_FIX)&&$(ESLINT_FIX)"

check_migrations: test_build
	$(COMPOSE_TEST) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_CHECK_MIGRATIONS)"

check: test_build
	$(COMPOSE_TEST) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_CHECK_MIGRATIONS)&&$(PYTHON_CHECK_MIGRATIONS)&&$(BLACK_CHECK)&&$(FLAKE8)&&$(ESLINT)&&$(PYTHON_TEST)"

checkfast: test_build
	$(COMPOSE_TEST) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_CHECK_MIGRATIONS)&&$(PYTHON_CHECK_MIGRATIONS)&&$(BLACK_CHECK)&&$(FLAKE8)&&$(ESLINT)&&$(PYTHON_TEST_FAST)"

compose_build: build ssl
	$(COMPOSE)  build

compose_kill:
	$(COMPOSE) kill

compose_rm:
	$(COMPOSE) rm -f

volumes_rm:
	docker volume ls -q | xargs docker volume rm

kill: compose_kill compose_rm volumes_rm
	echo "All containers removed!"

up: compose_kill compose_build
	$(COMPOSE) up

makemigrations: compose_build
	$(COMPOSE) run app python manage.py makemigrations

migrate: compose_build
	$(COMPOSE) run app sh -c "$(WAIT_FOR_DB) python manage.py migrate"

createuser: compose_build
	$(COMPOSE) run app python manage.py createsuperuser

load_locales_countries: compose_build
	$(COMPOSE) run app python manage.py load-locales-countries

load_dummy_experiments: compose_build
	$(COMPOSE) run app python manage.py load-dummy-experiments

shell: compose_build
	$(COMPOSE) run app python manage.py shell

dbshell: compose_build
	$(COMPOSE) run app python manage.py dbshell

bash: compose_build
	$(COMPOSE) run app bash

refresh: kill migrate load_locales_countries load_dummy_experiments

COMPOSE_FULL = docker-compose -f docker-compose.yml -f docker-compose-full.yml

# experimenter + delivery console + normandy stack
compose_build_all: build ssl
	 $(COMPOSE_FULL) build

up_all: compose_build_all
	$(COMPOSE_FULL) up

normandy_shell: compose_build_all
	$(COMPOSE_FULL) run normandy ./manage.py shell

COMPOSE_INTEGRATION = docker-compose -p experimenter_integration -f docker-compose.yml -f docker-compose.integration-test.yml

# integration tests
integration_kill:
	$(COMPOSE_INTEGRATION) kill
	$(COMPOSE_INTEGRATION) rm -f

integration_build: integration_kill ssl build
	$(COMPOSE_INTEGRATION) build
	$(COMPOSE_INTEGRATION) run app sh -c "$(WAIT_FOR_DB) python manage.py migrate;python manage.py load-locales-countries;python manage.py createsuperuser --username admin --email admin@example.com --noinput"

integration_shell: integration_build
	$(COMPOSE_INTEGRATION) run firefox bash

integration_up_shell:
	$(COMPOSE_INTEGRATION) run firefox bash

integration_up_detached: integration_build
	$(COMPOSE_INTEGRATION) up -d

integration_up: integration_build
	$(COMPOSE_INTEGRATION) up

integration_test_run: integration_build
	$(COMPOSE_INTEGRATION) run firefox tox -c tests/integration

integration_test: compose_kill integration_test_run integration_kill
	echo "Firefox tests complete!"
