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
	docker-compose -f docker-compose-test.yml run app sh -c "/app/bin/wait-for-it.sh db:5432 -- pytest -vvvv --cov --cov-report term-missing"

test-watch: compose_build
	docker-compose -f docker-compose-test.yml run app sh -c "/app/bin/wait-for-it.sh db:5432 -- ptw -- --testmon --show-capture=no --disable-warnings"

integration_test: migrate load_locales_countries ssl
	docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml up -d
	docker-compose -f docker-compose.yml -f docker-compose.integration-test.yml exec firefox tox -c tests/integration

lint: test_build
	docker-compose -f docker-compose-test.yml run app flake8 .

black_check: test_build
	docker-compose -f docker-compose-test.yml run app black -l 79 --check .

black_fix: test_build
	docker-compose -f docker-compose-test.yml run app black -l 79 .

code_format: black_fix
	echo "Code Formatted"

check_migrations: test_build
	docker-compose -f docker-compose-test.yml run app sh -c "/app/bin/wait-for-it.sh db:5432 -- python manage.py makemigrations --check --dry-run --noinput"

check: test_build check_migrations black_check lint test
	echo "Success"

compose_build: build ssl
	docker-compose build

compose_kill:
	docker-compose kill

up: compose_kill compose_build
	docker-compose up

gunicorn: compose_build
	docker-compose -f docker-compose.yml -f docker-compose-gunicorn.yml up

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

kill:
	docker ps -a -q | xargs docker kill;docker ps -a -q | xargs docker rm

refresh: kill migrate load_locales_countries load_dummy_experiments
