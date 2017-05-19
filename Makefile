secretkey:
	openssl rand -hex 24

build:
	./scripts/build.sh

compose_build: build
	docker-compose build

up: compose_build
	docker-compose up

test: compose_build
	docker-compose run app sh -c "/app/bin/wait-for-it.sh db:5432 -- coverage run manage.py test;coverage report -m --fail-under=100;coveralls"

lint: compose_build
	docker-compose run app flake8 .

check: compose_build lint test
	echo "Success"

makemigrations: compose_build
	docker-compose run app python manage.py makemigrations

migrate: compose_build
	docker-compose run app python manage.py migrate

createuser: compose_build
	docker-compose run app python manage.py createsuperuser

shell: compose_build
	docker-compose run app python manage.py shell

dbshell: compose_build
	docker-compose run app python manage.py dbshell

bash: compose_build
	docker-compose run app bash

kill:
	docker ps -a -q | xargs docker kill;docker ps -a -q | xargs docker rm
