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

compose_rm:
	docker-compose rm -f

kill: compose_kill compose_rm
	echo "All containers removed!"

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


refresh: kill migrate load_locales_countries load_dummy_experiments

# integration tests
integration_kill:
	docker-compose -p experimenter_integration -f docker-compose.integration-test.yml kill
	docker-compose -p experimenter_integration -f docker-compose.integration-test.yml rm -f

integration_build: build
	docker-compose -p experimenter_integration -f docker-compose.integration-test.yml build 
	docker-compose -p experimenter_integration -f docker-compose.integration-test.yml run app sh -c "/app/bin/wait-for-it.sh db:5432 -- python manage.py migrate;python manage.py load-locales-countries"

integration_shell: integration_build
	docker-compose -p experimenter_integration -f docker-compose.integration-test.yml run firefox bash 

integration_up_detached: integration_build
	docker-compose -p experimenter_integration -f docker-compose.integration-test.yml up -d

integration_up: integration_build
	docker-compose -p experimenter_integration -f docker-compose.integration-test.yml up

integration_test: integration_kill ssl integration_build create_integration_test_user
	docker-compose -p experimenter_integration -f docker-compose.integration-test.yml run firefox tox -c tests/integration

create_integration_test_user: integration_up
	docker-compose -p experimenter_integration -f docker-compose.integration-test.yml run app python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')"