#!/bin/bash

set -e

version=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`

architecture=`uname -m`

if [ $architecture == 'aarch64' ]; then
  file='chromedriver_mac_arm64.zip'
else
  file='chromedriver_linux64.zip'
fi

url="http://chromedriver.storage.googleapis.com/${version}/${file}"

wget -c -N ${url} && unzip ${file}
