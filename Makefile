build: 
	./scripts/build.sh

compose_build: build
	docker-compose build

up: compose_build
	docker-compose up

test: compose_build
	docker-compose run app python /app/manage.py test

lint: compose_build
	docker-compose run app flake8 .

check: compose_build lint test
	echo "Success"

migrate: compose_build
	docker-compose run app python manage.py migrate

shell: compose_build
	docker-compose run app python manage.py shell 
