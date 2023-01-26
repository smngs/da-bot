FROM archlinux:latest
USER root

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP.UTF-8
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

RUN mkdir -p /root/src
COPY requirements.txt /root/src
WORKDIR /root/src

RUN pacman -Syu --noconfirm && \
  pacman -S --noconfirm vim less python3 python-pip chromium noto-fonts noto-fonts-cjk noto-fonts-emoji

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt
