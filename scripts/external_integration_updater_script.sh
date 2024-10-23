#!/bin/bash

TASKCLUSTER_API="https://firefox-ci-tc.services.mozilla.com/api/index/v1"
WHAT_TRAIN_IS_IT_NOW_API="https://whattrainisitnow.com/api/firefox/releases/"
FENNEC_GITHUB_API="https://api.github.com/repos/mozilla-mobile/firefox-ios"
CURLFLAGS=("--proto" "=https" "--tlsv1.2" "-sS")

git checkout main
git checkout main
git pull origin main
git checkout -B check_external_firefox_integrations
firefox_types=("fenix_beta" "fenix_nightly" "fennec_release" "fennec_beta" "desktop_beta" "desktop_release")

fetch_task_info() {
    local release_version=$(curl "${CURLFLAGS[@]}" "${WHAT_TRAIN_IS_IT_NOW_API}" | jq 'to_entries | last | .key')
    local major_version="$(echo "$release_version" | cut -d'.' -f1 | tr -d '"')"
    local variant=$1
    local index_base=""
    local namespace=""
    local env_file=""
    local task_id=""
    
    case "$variant" in
        fenix_release)
            index_base="mobile.v3.firefox-android.apks.fenix-release.latest"
            namespace="mobile.v3.firefox-android.apks.fenix-release.latest.x86_64"
            env_file="firefox_fenix_release_build.env"
            ;;
        desktop_beta)
            index_base="gecko.v2.mozilla-beta.latest.firefox"
            namespace="gecko.v2.mozilla-beta.latest.firefox.linux64-debug"
            env_file="firefox_desktop_beta_build.env"
            ;;
        desktop_release)
            # Fetch release version separately 
            # release_version=$(curl "${CURLFLAGS[@]}" "${WHAT_TRAIN_IS_IT_NOW_API}" | jq 'to_entries | last | .key')
            echo "FIREFOX_DESKTOP_RELEASE_VERSION_ID ${release_version}"
            echo "FIREFOX_DESKTOP_RELEASE_VERSION_ID=${release_version}" > firefox_desktop_release_build.env
            mv firefox_desktop_release_build.env experimenter/tests
            return
            ;;
        fenix_beta)
            index_base="mobile.v3.firefox-android.apks.fenix-beta.latest"
            namespace="mobile.v3.firefox-android.apks.fenix-beta.latest.x86_64"
            env_file="firefox_fenix_beta_build.env"
            ;;
        fenix_nightly)
            index_base="mobile.v3.firefox-android.apks.fenix-nightly.latest"
            namespace="mobile.v3.firefox-android.apks.fenix-nightly.latest.x86_64"
            env_file="firefox_fenix_nightly_build.env"
            ;;
        fennec_release)
            version=$(curl "${CURLFLAGS[@]}" "${FENNEC_GITHUB_API}/releases" | jq '.[0].name')
            branch=$(curl "${CURLFLAGS[@]}" "${FENNEC_GITHUB_API}/releases" | jq '.[0].target_commitish')
            echo "FIREFOX_FENNEC_RELEASE_VERSION_ID ${version}"
            echo "FIREFOX_FENNEC_RELEASE_VERSION_ID=${version}" > firefox_fennec_release_build.env
            echo "BRANCH=${branch}" >> firefox_fennec_release_build.env
            echo "# Firefox version is ${release_version}" >> firefox_fennec_release_build.env
            mv firefox_fennec_release_build.env experimenter/tests
            return
            ;;
        fennec_beta)
            check_branches() {
                local protected_flag="$1"
                version=$(curl "${CURLFLAGS[@]}" "${FENNEC_GITHUB_API}/branches?protected=${protected_flag}&per_page=100" | jq --argjson major "$major_version" 'map(select(.name=="release/v" + ($major + 1 | tostring)).name)[]')
                echo $version
            }

            version=$(check_branches "false")

            if [ -z "$version" ]; then
                version=$(check_branches "true")
            fi

            echo "FIREFOX_FENNEC_BETA_VERSION_ID ${version}"
            echo "FIREFOX_FENNEC_BETA_VERSION_ID=${version}" > firefox_fennec_beta_build.env
            echo "BRANCH=${version}" >> firefox_fennec_beta_build.env
            echo "# Firefox version is ${release_version}" >> firefox_fennec_beta_build.env
            mv firefox_fennec_beta_build.env experimenter/tests
            return
            ;;
        *)
            echo "Unknown variant: ${variant}. Please specify a valid variant."
            return
            ;;
    esac

    # Fetch the task ID for the given variant and namespace
    task_id=$(curl "${CURLFLAGS[@]}" "${TASKCLUSTER_API}/tasks/${index_base}" | \
        jq --arg namespace "$namespace" '.tasks[] | select(.namespace == $namespace) | .taskId')

    echo "FIREFOX_${variant^^}_TASK_ID TASK ID ${task_id}"
    
    # Create the environment file
    echo "FIREFOX_${variant^^}_TASK_ID=${task_id}" > "${env_file}"

    # Move the environment file to the experimenter/tests directory
    mv "${env_file}" experimenter/tests
}

for name in "${firefox_types[@]}"
do
    CURRENT_BUILD_ID=$(cat experimenter/tests/firefox_${name}_build.env | grep -oP '(?<=TASK_ID=).*|(?<=VERSION_ID=).*')
    fetch_task_info $name
    LATEST_BUILD_ID=$(cat experimenter/tests/firefox_${name}_build.env | grep -oP '(?<=TASK_ID=).*|(?<=VERSION_ID=).*')
    if [[ "${CURRENT_BUILD_ID}" != "${LATEST_BUILD_ID}" ]]; then
        echo "Adding firefox_${name}_build.env" 
    fi
done

if (($(git status --porcelain | wc -c) > 0)); then
    git add .
    git commit -m "chore(nimbus): Check external firefox integrations and task ids and versions"
    git push origin -f check_external_firefox_integrations
    gh pr create -t "chore(nimbus):  Check external firefox integrations and task ids and versions" -b "" --base main --head check_external_firefox_integrations --repo mozilla/experimenter || echo "PR already exists, skipping"
else
    echo "No config changes, skipping"
fi
