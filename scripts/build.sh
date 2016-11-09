#/bin/bash
./scripts/echo_version_json.sh > ./app/version.json
docker build -f app/Dockerfile -t app:build app/ 
docker build -f app/Dockerfile.dev -t app:dev app/
