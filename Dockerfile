FROM python:3.10
USER root

RUN apt-get update
RUN apt-get -y install locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
RUN apt-get install -y vim less ffmpeg

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

RUN mkdir -p /root/src
COPY requirements.txt /root/src
COPY scripts/install_chromium.sh /root/src
WORKDIR /root/src

RUN apt -y update
RUN apt -y install x11vnc xvfb fluxbox wget wmctrl gnupg2 fonts-noto fonts-noto-cjk 

RUN ./install_chromium.sh

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt
