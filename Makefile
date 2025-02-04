# Makefile

# Load environment variables
include Makefile.env
export $(shell sed 's/=.*//' Makefile.env)

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
	docker compose --env-file docker-compose.env --profile all build api

.PHONY: run
run: build docker-run

# Run a single instance of the application without load balancing on Docker
.PHONY: docker-run
docker-run: 
	docker compose --env-file docker-compose.env --profile all up -d

# Run a cluster with load balancing on Docker
.PHONY: docker-cluster
docker-cluster: 
	docker compose --env-file docker-compose.env up --profile all -d --scale api=${CLUSTER_SIZE}

# Stop all test docker containers
.PHONY: docker-stop
docker-stop:
	docker compose --env-file docker-compose.env --profile all down

# Stop all running containers
.PHONY: stop
stop: docker-stop

# the following make cmd are not official, use for adhoc api testing

docker-local-dev: build
	docker compose --env-file docker-compose.env --profile db up

docker-test:
	@curl -sXGET 'http://localhost:${LOAD_BALANCER_PORT}' | jq .

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