# Makefile
SHELL := /bin/bash

# Load environment variables
export $(shell sed 's/=.*//' .env)
include .env

# Default target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make build				Build the Docker images"
	@echo "  make run				Standard run of the application as containers"
	@echo "  make run-db			Run only Redis & Postgres containers for local debugging"
	@echo "  make run-cluster		Run a cluster with load balancing on Docker"
	@echo "  make stop				Stop all running containers"
	@echo "  make venv-setup		Setup local development environment"
	@echo "  make debug				Launch single instances of containers setup for remote debugging"

# Build the Docker images
.PHONY: build
build:
	docker compose --profile all build api worker

# Run a single instance of the application without load balancing on Docker
.PHONY: run
run: build
	MIN_LOG_LEVEL=${MIN_LOG_LEVEL} API_CLUSTER_SIZE=1 WORKER_CLUSTER_SIZE=1 \
		docker compose --profile all up

# Run a cluster with load balancing on Docker
.PHONY: run-cluster
run-cluster: build
	MIN_LOG_LEVEL=${MIN_LOG_LEVEL} API_DELAY_MIN=0 API_DELAY_MAX=0 WORKER_DELAY_MIN=0 WORKER_DELAY_MAX=0 \
		docker compose --profile all up

.PHONY: run-db
run-db: build
	docker compose --profile db up

# Stop all running containers
.PHONY: stop
stop:
	docker compose --profile all down

# the following scripts are meant for local development & debugging, not required to run the application in docker

# this setup ensure vscode can run the application in debug mode and all required linter passes
.PHONY: venv-setup
venv-setup: requirements
	@(python3 -m venv .venv && \
		source .venv/bin/activate && \
		pip3 install -r requirements.txt && \
		rm requirements.txt)

# remove the virutual environment for this project completely
venv-clean:
	@(rm -rf .venv)

# create a transient ./requirements.txt file for pip to install all dependencies
requirements:
	@(rm -f requirements.txt && \
		cat shared_lib/requirements.txt > combined_requirements.txt && \
		echo '' >> combined_requirements.txt && \
        cat api/requirements.txt >> combined_requirements.txt && \
		echo '' >> combined_requirements.txt && \
        cat worker/requirements.txt >> combined_requirements.txt && \
		echo '' >> combined_requirements.txt && \
        cat ci_requirements.txt >> combined_requirements.txt && \
		echo '' >> combined_requirements.txt && \
		cat loader/requirements.txt >> combined_requirements.txt && \
		echo '' >> combined_requirements.txt && \
        sort -u combined_requirements.txt > requirements.txt && \
		rm combined_requirements.txt)

# combine all requirements files into a single file and install them, then remove it after
# make sure you activate the virtual environment before running this command
pip-install: requirements
	@(pip3 install -r requirements.txt && rm requirements.txt)

# this launch single instances of API & worker with a single thread
.PHONY: debug
debug: build
	MIN_LOG_LEVEL=DEBUG DEBUG_PAUSE=$(DEBUG_PAUSE) \
		API_CLUSTER_SIZE=1 WORKER_CLUSTER_SIZE=1 WORKER_THREADS=1 \
		docker compose -f docker-compose.yml -f docker-compose.debug.yml --profile all up

# curl quick health checks

check-api:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color'

check-worker:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/worker'

check-nginx:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}'

# curl api input tests

test-color-match:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/match?name=light+blue'

test-color-match2:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/match?name=green'

test-hex-match:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/match?name=ffffff'

test-hex-match2:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/match?name=000'

test-color-names:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/names'

test-color-error:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/match?name=er'

# locust load testing

# only hit load endpoints
load-ping:
	@locust --headless -f loader/ping_only.py -u ${LOCUST_USERS} -r ${LOCUST_SPAWN_RATE} \
		--host='http://localhost:${LOAD_BALANCER_PORT}'

# hit all endpoints all at once
load-test:
	API_DELAY_MIN=$(API_DELAY_MIN) API_DELAY_MAX=$(API_DELAY_MAX) \
	WORKER_DELAY_MIN=$(WORKER_DELAY_MIN) WORKER_DELAY_MAX=$(WORKER_DELAY_MAX) \
		locust --headless -f loader/color_endpoints.py -u ${LOCUST_USERS} -r ${LOCUST_SPAWN_RATE} \
			--host='http://localhost:${LOAD_BALANCER_PORT}'
