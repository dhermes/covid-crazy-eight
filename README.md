# `covid-crazy-eight`

> Bare Bones Webapp to Play Crazy Eights with friends while quarantines

To run

```
DEBUG=true PLAYERS=Joe,Eve,Tim python src/app.py
```

I'll probably cut a lot of corners while making this. To build and run in
Docker (which I'll probably utilize for Google Cloud Run)

```
docker build --tag dhermes/covid-crazy-eight:latest --file Dockerfile .
docker run \
  --rm \
  --interactive \
  --tty \
  --env DEBUG=true \
  --env PLAYERS=Joe,Eve,Tim \
  --publish 15071:15071 \
  dhermes/covid-crazy-eight:latest
```
