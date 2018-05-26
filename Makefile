secretkey:
	openssl rand -hex 24

build:
	./scripts/build.sh

compose_build: build ssl
	docker-compose build

up: compose_build
	docker-compose up

gunicorn: compose_build
	docker-compose -f docker-compose.yml -f docker-compose-gunicorn.yml up

test: compose_build
	docker-compose run app sh -c "/app/bin/wait-for-it.sh db:5432 -- coverage run manage.py test;coverage report -m --fail-under=100"

lint: compose_build
	docker-compose run app flake8 .

black: compose_build
	docker-compose run app black -l 79 .

check: compose_build lint black test
	echo "Success"

makemigrations: compose_build
	docker-compose run app python manage.py makemigrations

migrate: compose_build
	docker-compose run app sh -c "/app/bin/wait-for-it.sh db:5432 -- python manage.py migrate"

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


ssl: nginx/key.pem nginx/cert.pem

nginx/key.pem:
	openssl genrsa -out nginx/key.pem 4096

nginx/cert.pem: nginx/key.pem
	openssl req -new -x509 -nodes -sha256 -key nginx/key.pem \
		-subj "/C=US/ST=California/L=Mountain View/O=Mozilla/CN=experiment_local" \
		> nginx/cert.pem
