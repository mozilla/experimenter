#/bin/sh
./scripts/echo_version_json.sh > ./app/version.json
docker build -f app/Dockerfile -t app:build app/
