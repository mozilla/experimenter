#!/usr/bin/env bash

set -ex
apt-get -qqy update && apt-get -qqy install sudo
export SQLCIPHER_LIB_DIR=/code/app/tests/integration/application-services/libs/desktop/linux-x86-64/sqlcipher/lib
export SQLCIPHER_INCLUDE_DIR=/code/app/tests/integration/application-services/libs/desktop/linux-x86-64/sqlcipher/include
export NSS_DIR=/code/app/tests/integration/application-services/libs/desktop/linux-x86-64/nss
export NSS_STATIC=1
apt-get -qqy update && apt-get -qqy --no-install-recommends install tox git curl
apt-get update -qqy && apt-get -qqy install gyp ninja-build zlib1g-dev tclsh
curl https://sh.rustup.rs -sSf | bash -s -- -y
echo 'source $HOME/.cargo/env' >> $HOME/.bashrc
export PATH="/root/.cargo/bin:${PATH}"
git clone https://github.com/mozilla/application-services
python3 -V
cd application-services/
git submodule init
git submodule update --recursive
curl https://sh.rustup.rs -sSf | bash -s -- -y
echo 'source $HOME/.cargo/env' >> $HOME/.bashrc
source $HOME/.cargo/env
./libs/verify-desktop-environment.sh
cargo build
cargo build --manifest-path megazords/full/Cargo.toml --release
cargo uniffi-bindgen generate components/nimbus/src/nimbus.udl --language python
cd ..
mv -f application-services/components/nimbus/src/nimbus.py application-services/components/nimbus/src/nimbus_rust.py
mv application-services/target/release/libmegazord.so application-services/components/nimbus/src/libuniffi_nimbus.so