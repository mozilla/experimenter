#/bin/sh
./scripts/build.sh
docker build --target deploy -f app/Dockerfile -t app:deploy app/