#!/bin/sh
#
# Takes a version as the 1st parameter and
# writes it into the VERSION file.

OLD_VERSION=$(cat ./schemas/VERSION)

if [ "$#" -ne 1 ]; then
  echo "USAGE: ./set_schemas_version.sh <version>"
  echo "<version> is the desired version of the package"
  echo "Version scheme is CalVer (yyyy.m.#)"
  echo
  echo "Current version is $OLD_VERSION"

  exit 1
fi

NEW_VERSION=$1

echo "Setting new version to ${NEW_VERSION}..."
echo "  (old version was ${OLD_VERSION})"

echo "${NEW_VERSION}" > ./schemas/VERSION
echo
echo "Done."
echo

