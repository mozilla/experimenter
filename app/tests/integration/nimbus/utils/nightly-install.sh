set +x
echo "Installing the Latest Nightly"
apt-get update -qqy
rm -rf /var/lib/apt/lists/* /var/cache/apt/*
wget --no-verbose -O /tmp/firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-nightly-latest-ssl&os=linux64&lang=en-US"
rm -rf /opt/firefox-latest
tar -C /opt -xjf /tmp/firefox.tar.bz2
rm /tmp/firefox.tar.bz2
ln -fs /opt/firefox/firefox /usr/bin/firefox
