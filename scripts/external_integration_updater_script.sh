#!/bin/bash

git checkout main
git pull origin main
git checkout -B check_external_firefox_integrations
firefox_types=("fenix" "desktop-beta" "desktop-release")
for name in "${firefox_types[@]}"
do
    CURRENT_BUILD_ID=$(cat experimenter/tests/firefox-$name-build.env | grep -oP '(?<=TASK_ID=).*')
    ./scripts/update-firefox-keys.sh $name
    LATEST_BUILD_ID=$(cat experimenter/tests/firefox-$name-build.env | grep -oP '(?<=TASK_ID=).*')
    if [[ "${CURRENT_BUILD_ID}" != "${LATEST_BUILD_ID}" ]]; then
        echo "Adding firefox-$name-build.env" 
    fi
done

if (($(git status --porcelain | wc -c) > 0)); then
    git add .
    git commit -m "chore(nimbus): Check external firefox integrations and update keys"
    git push origin -f check_external_firefox_integrations
    gh pr create -t "chore(nimbus): Check external firefox integrations and update keys" -b "" --base main --head check_external_firefox_integrations --repo mozilla/experimenter || echo "PR already exists, skipping"
else
    echo "No config changes, skipping"
fi
