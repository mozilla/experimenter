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

test_build: build
	docker-compose -f docker-compose-test.yml build

test: test_build
	docker-compose -f docker-compose-test.yml run app sh -c "/app/bin/wait-for-it.sh db:5432 -- pytest -vvvv --cov --cov-report term-missing --show-capture=no"

test-watch: compose_build
	docker-compose -f docker-compose-test.yml run app sh -c "/app/bin/wait-for-it.sh db:5432 -- ptw -- --testmon --show-capture=no --disable-warnings"

eslint_assets: test_build
	docker-compose -f docker-compose-test.yml run app sh -c "yarn run lint"

eslint_fix: test_build
	docker-compose -f docker-compose-test.yml run app sh -c "yarn run lint-fix"

lint: test_build
	docker-compose -f docker-compose-test.yml run app flake8 .

black_check: test_build
	docker-compose -f docker-compose-test.yml run app black -l 90 --check .

black_fix: test_build
	docker-compose -f docker-compose-test.yml run app black -l 90 .

code_format: black_fix eslint_fix
	echo "Code Formatted"

check_migrations: test_build
	docker-compose -f docker-compose-test.yml run app sh -c "/app/bin/wait-for-it.sh db:5432 -- python manage.py makemigrations --check --dry-run --noinput"

check: test_build check_migrations black_check lint eslint_assets test
	echo "Success"

compose_build: build ssl
	docker-compose build

compose_kill:
	docker-compose kill

compose_rm:
	docker-compose rm -f

kill: compose_kill compose_rm
	echo "All containers removed!"

up: compose_kill compose_build
	docker-compose up

makemigrations: compose_build
	docker-compose run app python manage.py makemigrations

migrate: compose_build
	docker-compose run app sh -c "/app/bin/wait-for-it.sh db:5432 -- python manage.py migrate"

createuser: compose_build
	docker-compose run app python manage.py createsuperuser

load_locales_countries: compose_build
	docker-compose run app python manage.py load-locales-countries

load_dummy_experiments: compose_build
	docker-compose run app python manage.py load-dummy-experiments

shell: compose_build
	docker-compose run app python manage.py shell

dbshell: compose_build
	docker-compose run app python manage.py dbshell

bash: compose_build
	docker-compose run app bash

refresh: kill migrate load_locales_countries load_dummy_experiments

# experimenter + delivery console + normandy stack
compose_build_all: build ssl
	docker-compose -f docker-compose.yml -f docker-compose-full.yml build

up_all: compose_build_all
	docker-compose -f docker-compose.yml -f docker-compose-full.yml up

normandy_shell: compose_build_all
	docker-compose -f docker-compose.yml -f docker-compose-full.yml run normandy ./manage.py shell

# integration tests
integration_kill:
	docker-compose -p experimenter_integration -f docker-compose.yml -f docker-compose.integration-test.yml kill
	docker-compose -p experimenter_integration -f docker-compose.yml -f docker-compose.integration-test.yml rm -f

integration_build: integration_kill ssl build
	docker-compose -p experimenter_integration -f docker-compose.yml -f docker-compose.integration-test.yml build
	docker-compose -p experimenter_integration -f docker-compose.yml -f docker-compose.integration-test.yml run app sh -c "/app/bin/wait-for-it.sh db:5432 -- python manage.py migrate;python manage.py load-locales-countries;python manage.py createsuperuser --username admin --email admin@example.com --noinput"

integration_shell: integration_build
	docker-compose -p experimenter_integration -f docker-compose.yml -f docker-compose.integration-test.yml run firefox bash

integration_up_shell:
	docker-compose -p experimenter_integration -f docker-compose.yml -f docker-compose.integration-test.yml run firefox bash

integration_up_detached: integration_build
	docker-compose -p experimenter_integration -f docker-compose.yml -f docker-compose.integration-test.yml up -d

integration_up: integration_build
	docker-compose -p experimenter_integration -f docker-compose.yml -f docker-compose.integration-test.yml up

integration_test: integration_build
	docker-compose -p experimenter_integration -f docker-compose.yml -f docker-compose.integration-test.yml run firefox tox -c tests/integration
