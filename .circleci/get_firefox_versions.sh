#!/bin/bash -x
set -e

OUTPUT=/home/circleci/experimenter
touch $OUTPUT/new_versions.txt
VERSIONS_FILE=$OUTPUT/new_versions.txt

# Firefox
apt-get update
FIREFOX_RELEASE_PKG=$(apt-cache madison firefox | head -n1 | awk '{ print $3 }')
FIREFOX_RELEASE_VER=$(echo $FIREFOX_PKG | cut -d"." -f1)

# Firefox Beta
add-apt-repository --yes ppa:mozillateam/firefox-next && apt-get update
FIREFOX_BETA_PKG=$(apt-cache madison firefox | head -n1 | awk '{ print $3 }')
FIREFOX_BETA_VER=$(echo $FIREFOX_BETA_PKG | cut -d"." -f1)


# OUTPUT
echo FIREFOX_PKG=$FIREFOX_RELEASE_PKG > $VERSIONS_FILE
echo FIREFOX_VER=$FIREFOX_RELEASE_VER >> $VERSIONS_FILE
echo FIREFOX_BETA_VER=$FIREFOX_BETA_VER >> $VERSIONS_FILE
echo FIREFOX_BETA_PKG=$FIREFOX_BETA_PKG >> $VERSIONS_FILE

cat $VERSIONS_FILE

chmod -R 777 $OUTPUT