./scripts/echo_version_json.sh > ./app/experimenter/version.json
cp ./app/experimenter/version.json ./app/version.json
git log -n 1 --no-color --pretty='%s' > ./app/commit-summary.txt
git log -n 1 --no-color --pretty=medium > ./app/commit-description.txt
