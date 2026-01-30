# Local development environment

## Build the application containers and launch services

From the root directory of this repo, run the following to build containers and launch the web app:

```bash
$ docker compose --file container/docker-compose.yaml up --build
```

Terminate the application with

```bash
$ docker compose --file container/docker-compose.yaml down
```

