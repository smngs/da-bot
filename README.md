# da-bot

Discord bot for **da**-server! 

## Require

- docker
- docker-compose

> Currently, this Docker image only works on `x86_64` architecture computers; support for `arm64` (Apple M1) is TBD.

## Usage

```
$ touch secret.env && echo "DISCORD_API_KEY=hogehoge" >> secret.env
$ docker-compose build
$ docker-compose up
```
