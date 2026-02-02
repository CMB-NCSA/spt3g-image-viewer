# Local development environment

## Configure application options

Create a `/container/.env` file with at minimum the following override values:

```bash
SPT3G_VIEWER_SECRET_KEY = "some randomly generated string"
SPT3G_VIEWER_USERNAME = "custom login username"
SPT3G_VIEWER_PASSWORD = "custom login password"
```

## Build the application containers and launch services

From the root directory of this repo, run the following to build containers and launch the web app:

```bash
$ docker compose --file container/docker-compose.yaml up --build
```

Terminate the application with

```bash
$ docker compose --file container/docker-compose.yaml down
```

