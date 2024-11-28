set +x
echo "Installing the Latest Nightly"
apt-get update -qqy
apt-get install -qqy xz-utils
rm -rf /var/lib/apt/lists/* /var/cache/apt/*
wget --no-verbose -O /tmp/firefox-latest "https://download.mozilla.org/?product=firefox-nightly-latest-ssl&os=linux64&lang=en-US"
rm -rf /opt/firefox-latest
tar -C /opt -xf /tmp/firefox-latest
rm /tmp/firefox-latest
ln -fs /opt/firefox/firefox /usr/bin/firefox
