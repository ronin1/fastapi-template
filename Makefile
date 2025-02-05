# Makefile
SHELL := /bin/bash

# Load environment variables
include .env
export $(shell sed 's/=.*//' .env)

# Default target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make build				Build the Docker images"
	@echo "  make run				Standard run of the application"
	@echo "  make docker-run		Run a single instance of the application on Docker"
	@echo "  make docker-cluster	Run a cluster with load balancing on Docker"
	@echo "  make docker-stop		Stop all running containers in Docker"
	@echo "  make stop				Stop all running containers"

# Build the Docker images
.PHONY: build
build:
	docker compose --profile all build api worker

.PHONY: run
run: build docker-run

# Run a single instance of the application without load balancing on Docker
.PHONY: docker-run
docker-run: 
	docker compose --profile all up

# Run a cluster with load balancing on Docker
.PHONY: docker-cluster
docker-cluster: 
	docker compose up --profile all --scale api=${CLUSTER_SIZE}

# Stop all test docker containers
.PHONY: docker-stop
docker-stop:
	docker compose --profile all down

# Stop all running containers
.PHONY: stop
stop: docker-stop

# the following make cmd are not official, use for adhoc api testing

local-setup:
	@(python3 -m venv .venv && \
		source .venv/bin/activate && \
		pip3 install -r shared_lib/requirements.txt && \
		pip3 install -r api/requirements.txt && \
		pip3 install -r worker/requirements.txt)

run-db: build
	docker compose --profile db up

docker-api-test:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color'

docker-worker-test:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/worker'

docker-loadbalancer-test:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}'

docker-color-match:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/match?name=light+blue'

docker-color-match2:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/match?name=green'

docker-hex-match:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/match?name=ffffff'

docker-hex-match2:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/match?name=000'

docker-color-names:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/names'

docker-color-error:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color/match?name=er'