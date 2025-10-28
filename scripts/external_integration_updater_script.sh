#!/bin/bash

TASKCLUSTER_API="https://firefox-ci-tc.services.mozilla.com/api/index/v1"
WHAT_TRAIN_IS_IT_NOW_API="https://whattrainisitnow.com/api/firefox/releases/"
FENNEC_GITHUB_API="https://api.github.com/repos/mozilla-mobile/firefox-ios"
CURLFLAGS=("--proto" "=https" "--tlsv1.2" "-sS")

git checkout main
git checkout main
git pull origin main
git checkout -B update_firefox_versions
firefox_types=("fenix_beta" "fennec_release" "fennec_beta" "desktop_beta" "desktop_release")


fetch_task_info() {
    local release_version=$(curl "${CURLFLAGS[@]}" "${WHAT_TRAIN_IS_IT_NOW_API}" | jq 'to_entries | last | .key')
    local major_version="$(echo "$release_version" | cut -d'.' -f1 | tr -d '"')"
    local variant=$1
    local index_base=""
    local namespace=""
    local env_file=""
    local task_id=""
    
    case "$variant" in
        desktop_release)
            # Fetch release version separately
            # release_version=$(curl "${CURLFLAGS[@]}" "${WHAT_TRAIN_IS_IT_NOW_API}" | jq 'to_entries | last | .key')
            echo "FIREFOX_DESKTOP_RELEASE_VERSION_ID ${release_version}"
            echo "FIREFOX_DESKTOP_RELEASE_VERSION_ID=${release_version}" > firefox_desktop_release_build.env
            mv firefox_desktop_release_build.env experimenter/tests
            return
            ;;
        desktop_beta)
            index_base="gecko.v2.mozilla-beta.latest.firefox"
            namespace="gecko.v2.mozilla-beta.latest.firefox.linux64-debug"
            env_file="firefox_desktop_beta_build.env"
            ;;
        fenix_release)
            index_base="gecko.v2.mozilla-release.latest.mobile"
            namespace="gecko.v2.mozilla-release.latest.mobile.fenix-release"
            env_file="firefox_fenix_release_build.env"
            ;;
        fenix_beta)
            index_base="gecko.v2.mozilla-beta.latest.mobile"
            namespace="gecko.v2.mozilla-beta.latest.mobile.fenix-beta"
            env_file="firefox_fenix_beta_build.env"
            ;;
        fennec_release)
            releases=$(curl "${CURLFLAGS[@]}" "${FENNEC_GITHUB_API}/releases" | jq '[.[] | select(.prerelease == false) | select(.name | test("^Firefox v[0-9]+\\.[0-9]+$"))][0]')
            version=$(echo "$releases" | jq -r '.name')
            branch=$(echo "$releases" | jq -r '.target_commitish')

            echo "FIREFOX_FENNEC_RELEASE_VERSION_ID ${version}"
            echo "FIREFOX_FENNEC_RELEASE_VERSION_ID=\"${version}\"" > firefox_fennec_release_build.env
            echo "BRANCH=\"${branch}\"" >> firefox_fennec_release_build.env
            echo "# Firefox version is ${release_version}" >> firefox_fennec_release_build.env
            mv firefox_fennec_release_build.env experimenter/tests
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
    git commit -m "chore(nimbus): Update Firefox Versions"
    git push origin -f update_firefox_versions
    gh pr create -t "chore(nimbus):  Update Firefox Versions" -b "" --base main --head update_firefox_versions --repo mozilla/experimenter || echo "PR already exists, skipping"
else
    echo "No config changes, skipping"
fi
