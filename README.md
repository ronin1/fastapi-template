# Python FastAPI Template with Nginx, Redis, & Postgres

Fork this repository and use it as the base for a barebone Python [FastAPI](https://fastapi.tiangolo.com) application.  The architecture of this app is setup as follow:

```text
[Nginx] -proxy--> [Py:API] -publish--> [Redis:List] <--consume- [Py:Worker] -insert--> [Postgres:Table]
```

## Why does this exists?

- I needed a dummy python app to test [OpenTofu](https://opentofu.org) & [K3S](https://k3s.io) locally
- The `API` & `Worker` app are both designed to be injected with artifical bounded random thread sleep to simulate work
- This will allow the use of a load tester & [Kubernestes](https://kubernetes.io/docs/home/) horizontal auto scalers like [KEDA](https://keda.sh)
- It can also be used as [FastAPI](https://fastapi.tiangolo.com) micro service code template to quickly to setup an API & accompanying background worker service that's backed by [Redis](https://redis.io/docs/latest/develop/clients/redis-py/) & [Postgres](https://github.com/MagicStack/asyncpg) in a producer-consumer pattern

## Running the App for the First Time

Assuming you have `Docker` installed properly with `make` and you're on Linux or a variant of Unix (like MacOS). To build & run the whole thing, simply execute the following from repository root path:

```sh
# this will build all local containers & launch docker-compose.yml
# nginx by default will listen on your machine's `localhost:8000`
[project_root]$ make run

# press Ctrl+C to stop. To truly shut down all containers, run:
[project_root]$ make stop

# all data will be removed from Redis & Postgres container with the above command
```

`make run` only run the standard configuration from `docker-compose.yml` which should have only 1 instance of `API` & 1 instance of `Worker`.

To simulate a miniature cluster, instead do `make run-cluster`. This takes the following values from `.env` file to launch 2 instances of `API` and `Worker`. Both are stil proxied (and load balanced) via `nginx` on port `8000`.

```env
API_CLUSTER_SIZE=2
WORKER_CLUSTER_SIZE=2
```

`API` and `Worker` container ports are not exposed to your local workstation at all, only `nginx`, `redis` & `postgres` are (for debugging). You can do health check using `curl` directly on `nginx` to check `nginx` health & `API` + `Worker` health as follow:

```sh
# to check nginx
$ curl -iXGET 'http://localhost:8000'

HTTP/1.1 200 OK
Server: nginx/1.27.3
Date: Wed, 05 Feb 2025 04:56:46 GMT
Content-Type: text/plain
Content-Length: 45
Connection: keep-alive
Content-Type: application/json

{"message": "Load Balancer say: Hello! 👋"}

# to check API
$ curl -iXGET 'http://localhost:8000/color'

HTTP/1.1 200 OK
Server: nginx/1.27.3
Date: Wed, 05 Feb 2025 04:57:06 GMT
Content-Type: application/json
Content-Length: 117
Connection: keep-alive

{"status":"OK","name":"color api","host":"ac95b94d48f3","boot":"2025-02-05T04:25:47.473431","alive":"0:31:19.263662"}

# to check Worker
$ curl -iXGET 'http://localhost:8000/worker'
```

If you're launching a cluster using `make run-cluster`, doing repeated health check on `API` or `Worker` will yield different `host` id, proving that `nginx` load balancer configuration is working as expected.

### Quick Tests

I added these make commands to help with testing. **NOTE** that all of these tests are basically using `curl` against `localhost:${LOAD_BALANCER_PORT}`.  You can find this value in `.env` file.

```sh
## pinging & health check:

# check load balancer health
[project_root]$ make check-nginx
# check API health
[project_root]$ make check-api
# check worker health
[project_root]$ make check-worker

## testing application by sending query to the color API

# color api match: light blue
[project_root]$ make test-color-match
# color api match: green
[project_root]$ make test-color-match2
# reverse api hex match: ffffff
[project_root]$ make test-hex-match
# short api hex match: fff
[project_root]$ make test-hex-match2
# get all Open Color base names
[project_root]$ make test-color-names
# send in a bad input to get a 400 by trying to match the color name: "er"
[project_root]$ make test-color-error
```

### Load Testing

Artifical thread sleep can be injected into both the `API` & the `Worker` app to simulate heavy work.  Both of these values can be changed in `.env` (along with the cluster size)

```env
# artifical delay settings. 
# Upper & lower bound can be the same value. Setting both to 0 disables delay.

API_DELAY_MIN=100
API_DELAY_MAX=150

WORKER_DELAY_MIN=100
WORKER_DELAY_MAX=150

# you can also change the cluster size for: make run-cluster

API_CLUSTER_SIZE=2
WORKER_CLUSTER_SIZE=2
```

## Debugging

VisualStudio Code configuration are checked in for easy debugging without any setup. This author assumes you're using Linux or some variation of Unix (MacOS).  Debugging might not work on Windows unless you're using Linux sub-system.

### Local Workstation Debug via Python Virtual Environment

To do this, you'll need Python 3.13+ installed & the latest VisualStudio code & these recommended (but optional) extensions:

- Python - by Microsoft
- Python Debugger - also by Microsoft
- autopep8 - also by Microsoft
- Back Formatter - you guest it, Microsoft
- Flake8 - Microsoft
- Gather - Microsoft
- isort - Microsoft
- Mypy Type Checker - Microsoft
- CMake Tools - Microsoft
- Makefile Tools - Microsoft
- Docker - Microsoft
- YAML - Mot Microsoft: Red Hat 😅

This is the simplest setup. To start, change directory to project root in your shell, then:

```sh
# do the initial setup if you haven't done it already. 
# It will create an virtual environment with all depdencies installed at ./.venv
[project_root]$ make local-setup

# if you're not running the above, active your virtual environment
[project_root]$ source .venv/bin/active

# assuming you have vscode console command setup as "code", launch it in the activated shell
[project_root]$ code .

# to launch just Redis & Postgres containers alone:
[project_root]$ make run-db
```

Once launched, there should be already 2 debuging profiles setup (under `.vscode/launch.json`) as:

- `Debug: API` - this will launch the API and attach it to port `3000`
- `Debug: Worker` - this will launch worker and attach it to port `3001`

**Note** that the above 2 debug profiles will need Redis & Postgres running or they will fail (API only needs Redis).  These profiles are designed to work with the exposed database ports.

### Container attach Debug via Python Remote Debugger

Since the code is running on Alpine Linux (not a typical distro for deskt-top use). Sometimes it's still best to debug & test the code within the container and observe its behavior within the actual OS being used in production.

This work is currently missing & will be added in future commits!
