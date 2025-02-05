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
	@echo "  make run				Standard run of the application as containers"
	@echo "  make run-db			Run only Redis & Postgres containers for local debugging"
	@echo "  make run-cluster	Run a cluster with load balancing on Docker"
	@echo "  make stop				Stop all running containers"

# Build the Docker images
.PHONY: build
build:
	docker compose --profile all build api worker

# Run a single instance of the application without load balancing on Docker
.PHONY: run
run: build
	docker compose --profile all up

# Run a cluster with load balancing on Docker
.PHONY: run-cluster
run-cluster: 
	docker compose up --profile all --scale api=${API_CLUSTER_SIZE} --scale worker=${WORKER_CLUSTER_SIZE}

.PHONY: run-db
run-db: build
	docker compose --profile db up

# Stop all running containers
.PHONY: stop
stop:
	docker compose --profile all down

# the following make cmd are not official, use for adhoc api testing

local-setup:
	@(python3 -m venv .venv && \
		source .venv/bin/activate && \
		pip3 install -r shared_lib/requirements.txt && \
		pip3 install -r api/requirements.txt && \
		pip3 install -r worker/requirements.txt)

check-api:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/color'

check-worker:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}/worker'

check-nginx:
	@curl -iXGET 'http://localhost:${LOAD_BALANCER_PORT}'

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