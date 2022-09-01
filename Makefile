SHELL = /bin/bash

WAIT_FOR_DB = /app/bin/wait-for-it.sh -t 30 db:5432 &&
WAIT_FOR_RUNSERVER = /app/bin/wait-for-it.sh -t 30 localhost:7001 &&

COMPOSE = docker-compose -f docker-compose.yml
COMPOSE_LEGACY = ${COMPOSE} -f docker-compose-legacy.yml
COMPOSE_TEST = docker-compose -f docker-compose-test.yml
COMPOSE_PROD = docker-compose -f docker-compose-prod.yml
COMPOSE_INTEGRATION = ${COMPOSE_PROD} -f docker-compose-integration-test.yml

JOBS = 4
PARALLEL = parallel --halt now,fail=1 --jobs ${JOBS} {} :::
NOCOLOR= \033[0m
RED = \033[0;31m
GREEN = \033[0;32m
PAD = -------------------------------------------------\n
COLOR_CHECK = && echo "${GREEN}${PAD}All Checks Passed\n${PAD}${NOCOLOR}" || (echo "${RED}${PAD}Some Checks Failed\n${PAD}${NOCOLOR}";exit 1)
PY_IMPORT_SORT =  python -m isort . --profile black
PY_IMPORT_CHECK =  python -m isort . --profile black --check
PYTHON_TEST = pytest --cov --cov-report term-missing
PYTHON_CHECK_MIGRATIONS = python manage.py makemigrations --check --dry-run --noinput
PYTHON_MIGRATE = python manage.py migrate
ESLINT_LEGACY = yarn workspace @experimenter/core lint
ESLINT_FIX_CORE = yarn workspace @experimenter/core lint-fix
ESLINT_NIMBUS_UI = yarn workspace @experimenter/nimbus-ui lint
ESLINT_FIX_NIMBUS_UI = yarn workspace @experimenter/nimbus-ui lint-fix
TYPECHECK_NIMBUS_UI = yarn workspace @experimenter/nimbus-ui lint:tsc

JS_TEST_LEGACY = yarn workspace @experimenter/core test
JS_TEST_NIMBUS_UI = CI=yes yarn workspace @experimenter/nimbus-ui test:cov
NIMBUS_SCHEMA_CHECK = python manage.py graphql_schema --out experimenter/nimbus-ui/test_schema.graphql&&diff experimenter/nimbus-ui/test_schema.graphql experimenter/nimbus-ui/schema.graphql || (echo GraphQL Schema is out of sync please run make generate_types;exit 1)
NIMBUS_TYPES_GENERATE = python manage.py graphql_schema --out experimenter/nimbus-ui/schema.graphql&&yarn workspace @experimenter/nimbus-ui generate-types
FLAKE8 = flake8 .
BLACK_CHECK = black -l 90 --check --diff . --exclude node_modules
BLACK_FIX = black -l 90 . --exclude node_modules
CHECK_DOCS = python manage.py generate_docs --check=true
GENERATE_DOCS = python manage.py generate_docs
LOAD_COUNTRIES = python manage.py loaddata ./experimenter/base/fixtures/countries.json
LOAD_LOCALES = python manage.py loaddata ./experimenter/base/fixtures/locales.json
LOAD_LANGUAGES = python manage.py loaddata ./experimenter/base/fixtures/languages.json
LOAD_FEATURES = python manage.py load_feature_configs
LOAD_DUMMY_EXPERIMENTS = [[ -z $$SKIP_DUMMY ]] && python manage.py load_dummy_experiments || echo "skipping dummy experiments"


JETSTREAM_CONFIG_URL = https://github.com/mozilla/jetstream-config/archive/main.zip
FEATURE_MANIFEST_DESKTOP_URL = https://hg.mozilla.org/mozilla-central/raw-file/tip/toolkit/components/nimbus/FeatureManifest.yaml
FEATURE_MANIFEST_FENIX_URL = https://raw.githubusercontent.com/mozilla-mobile/fenix/main/.experimenter.yaml
FEATURE_MANIFEST_FXIOS_URL = https://raw.githubusercontent.com/mozilla-mobile/firefox-ios/main/.experimenter.yaml
FEATURE_MANIFEST_FOCUS_ANDROID = https://raw.githubusercontent.com/mozilla-mobile/focus-android/main/.experimenter.yaml

ssl: nginx/key.pem nginx/cert.pem

nginx/key.pem:
	openssl genrsa -out nginx/key.pem 4096

nginx/cert.pem: nginx/key.pem
	openssl req -new -x509 -nodes -sha256 -key nginx/key.pem \
		-subj "/C=US/ST=California/L=Mountain View/O=Mozilla/CN=experiment_local" \
		> nginx/cert.pem

secretkey:
	openssl rand -hex 24

auth_gcloud:
	gcloud auth login --update-adc

jetstream_config:
	curl -LJ -o app/experimenter/outcomes/jetstream-config.zip $(JETSTREAM_CONFIG_URL)
	unzip -o -d app/experimenter/outcomes app/experimenter/outcomes/jetstream-config.zip
	rm -Rf app/experimenter/outcomes/jetstream-config-main/.scripts/

feature_manifests:
	curl -LJ --create-dirs -o app/experimenter/features/manifests/firefox-desktop.yaml $(FEATURE_MANIFEST_DESKTOP_URL)
	curl -LJ --create-dirs -o app/experimenter/features/manifests/fenix.yaml $(FEATURE_MANIFEST_FENIX_URL)
	curl -LJ --create-dirs -o app/experimenter/features/manifests/ios.yaml $(FEATURE_MANIFEST_FXIOS_URL)
	curl -LJ --create-dirs -o app/experimenter/features/manifests/focus-android.yaml $(FEATURE_MANIFEST_FOCUS_ANDROID)

fetch_external_resources: jetstream_config feature_manifests
	echo "External Resources Fetched"

update_kinto:
	docker pull mozilla/kinto-dist:latest

build_dev: ssl
	DOCKER_BUILDKIT=1 docker build --target dev -f app/Dockerfile -t app:dev --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from mozilla/experimenter:build_dev $$([[ -z "$${CIRCLECI}" ]] || echo "--progress=plain") app/

build_test: ssl
	DOCKER_BUILDKIT=1 docker build --target test -f app/Dockerfile -t app:test --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from mozilla/experimenter:build_test $$([[ -z "$${CIRCLECI}" ]] || echo "--progress=plain") app/

build_ui: ssl
	DOCKER_BUILDKIT=1 docker build --target ui -f app/Dockerfile -t app:ui --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from mozilla/experimenter:build_ui $$([[ -z "$${CIRCLECI}" ]] || echo "--progress=plain") app/

build_prod: build_ui ssl
	DOCKER_BUILDKIT=1 docker build --target deploy -f app/Dockerfile -t app:deploy --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from mozilla/experimenter:latest $$([[ -z "$${CIRCLECI}" ]] || echo "--progress=plain") app/

compose_stop:
	$(COMPOSE) kill || true
	$(COMPOSE_INTEGRATION) kill || true
	$(COMPOSE_PROD) kill || true

compose_rm:
	$(COMPOSE) rm -f -v || true
	$(COMPOSE_INTEGRATION) rm -f -v || true
	$(COMPOSE_PROD) rm -f -v || true

volumes_rm:
	docker volume prune -f

static_rm:
	rm -Rf app/node_modules
	rm -Rf app/experimenter/legacy/legacy-ui/core/node_modules/
	rm -Rf app/experimenter/nimbus-ui/node_modules/
	rm -Rf app/experimenter/legacy/legacy-ui/assets/
	rm -Rf app/experimenter/nimbus-ui/build/

kill: compose_stop compose_rm volumes_rm
	echo "All containers removed!"

check: build_test
	$(COMPOSE_TEST) run app sh -c '$(WAIT_FOR_DB) (${PARALLEL} "$(NIMBUS_SCHEMA_CHECK)" "$(PYTHON_CHECK_MIGRATIONS)" "$(CHECK_DOCS)" "${PY_IMPORT_CHECK}" "$(BLACK_CHECK)" "$(FLAKE8)" "$(ESLINT_LEGACY)" "$(ESLINT_NIMBUS_UI)" "$(TYPECHECK_NIMBUS_UI)" "$(JS_TEST_LEGACY)" "$(JS_TEST_NIMBUS_UI)" "$(JS_TEST_REPORTING)" "$(PYTHON_TEST)") ${COLOR_CHECK}'

pytest: build_test
	$(COMPOSE_TEST) run app sh -c '$(WAIT_FOR_DB) $(PYTHON_TEST)'

up: build_dev
	$(COMPOSE) up

up_legacy: build_dev
	$(COMPOSE_LEGACY) up

up_prod: build_prod
	$(COMPOSE_PROD) up

up_prod_detached: build_prod
	$(COMPOSE_PROD) up -d

up_db: build_dev
	$(COMPOSE) up db redis kinto autograph

up_django: build_dev
	$(COMPOSE) up nginx app worker beat db redis kinto autograph

up_detached: build_dev
	$(COMPOSE) up -d

generate_docs: build_dev
	$(COMPOSE) run app sh -c "$(GENERATE_DOCS)"

generate_types: build_dev
	$(COMPOSE) run app sh -c "$(NIMBUS_TYPES_GENERATE)"

code_format: build_dev
	$(COMPOSE) run app sh -c '${PARALLEL} "${PY_IMPORT_SORT};$(BLACK_FIX)" "$(ESLINT_FIX_CORE)" "$(ESLINT_FIX_NIMBUS_UI)"'

makemigrations: build_dev
	$(COMPOSE) run app python manage.py makemigrations

migrate: build_dev
	$(COMPOSE) run app sh -c "$(WAIT_FOR_DB) $(PYTHON_MIGRATE)"

bash: build_dev
	$(COMPOSE) run app bash

refresh: kill build_dev
	$(COMPOSE) run -e SKIP_DUMMY=$$SKIP_DUMMY app bash -c '$(WAIT_FOR_DB) $(PYTHON_MIGRATE)&&$(LOAD_LOCALES)&&$(LOAD_COUNTRIES)&&$(LOAD_LANGUAGES)&&$(LOAD_FEATURES)&&$(LOAD_DUMMY_EXPERIMENTS)'

dependabot_approve:
	echo "Install and configure the Github CLI https://github.com/cli/cli"
	gh pr list --author app/dependabot | awk '{print $$1}' | xargs -n1 gh pr review -a -b "@dependabot squash and merge"

# integration tests
integration_shell:
	$(COMPOSE_INTEGRATION) run firefox bash

integration_sdk_shell: build_prod
	$(COMPOSE_INTEGRATION) run rust-sdk bash

integration_vnc_up:
	$(COMPOSE_INTEGRATION) up

integration_vnc_up_detached:
	$(COMPOSE_INTEGRATION) up -d firefox

integration_test_legacy: build_prod
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION) run firefox sh -c "sudo apt-get -qqy update && sudo apt-get -qqy install tox;sudo chmod a+rwx /code/app/tests/integration/.tox;tox -c app/tests/integration -e integration-test-legacy $(TOX_ARGS) -- -n 2 $(PYTEST_ARGS)"

integration_test_nimbus: build_prod
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION) run firefox sh -c "if [ "$$UPDATE_FIREFOX_VERSION" = "true" ]; then sudo ./app/tests/integration/nimbus/utils/nightly-install.sh; fi; firefox -V; sudo apt-get -qqy update && sudo apt-get -qqy install tox;sudo chmod a+rwx /code/app/tests/integration/.tox;tox -c app/tests/integration -e integration-test-nimbus $(TOX_ARGS) -- $(PYTEST_ARGS)"

integration_test_nimbus_rust: build_prod
	MOZ_HEADLESS=1 $(COMPOSE_INTEGRATION) run rust-sdk sh -c "chmod a+rwx /code/app/tests/integration/.tox;tox -c app/tests/integration -e integration-test-nimbus-rust $(TOX_ARGS) -- -n 2 $(PYTEST_ARGS)"
