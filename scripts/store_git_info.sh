./scripts/echo_version_json.sh > ./experimenter/experimenter/version.json
git log -n 1 --no-color --pretty='%s' > ./experimenter/commit-summary.txt
git log -n 1 --no-color --pretty=medium > ./experimenter/commit-description.txt
