if [ `uname -m` = "aarch64" ]; then
  apt-get install -y \
    ca-certificates \
    sudo \
    libgbm1 \
    libnspr4 \
    libnss3 \
    xdg-utils \
    libwayland-server0 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libpango-1.0-0 \
    libxkbcommon0 \
    wget

  wget -P /tmp/ https://launchpad.net/~canonical-chromium-builds/+archive/ubuntu/stage/+files/chromium-browser_108.0.5359.71-0ubuntu0.18.04.5_arm64.deb
  wget -P /tmp/ https://launchpad.net/~canonical-chromium-builds/+archive/ubuntu/stage/+files/chromium-chromedriver_108.0.5359.71-0ubuntu0.18.04.5_arm64.deb
  wget -P /tmp/ https://launchpad.net/~canonical-chromium-builds/+archive/ubuntu/stage/+files/chromium-codecs-ffmpeg-extra_108.0.5359.71-0ubuntu0.18.04.5_arm64.deb
  wget -P /tmp/ https://launchpad.net/~canonical-chromium-builds/+archive/ubuntu/stage/+files/chromium-codecs-ffmpeg_108.0.5359.71-0ubuntu0.18.04.5_arm64.deb

  dpkg -i /tmp/chromium-codecs-ffmpeg_108.0.5359.71-0ubuntu0.18.04.5_arm64.deb
  dpkg -i /tmp/chromium-codecs-ffmpeg-extra_108.0.5359.71-0ubuntu0.18.04.5_arm64.deb
  dpkg -i /tmp/chromium-browser_108.0.5359.71-0ubuntu0.18.04.5_arm64.deb
  dpkg -i /tmp/chromium-chromedriver_108.0.5359.71-0ubuntu0.18.04.5_arm64.deb
else
  wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
  apt -y update
  apt -y install google-chrome-stable
fi
