#!/bin/bash
source .env 

set -e

if ! docker image inspect postgres >/dev/null 2>&1; then
    echo "Pulling postgres 17 image..."
    docker pull postgres:17;
else
    echo "Postgres image already present."
fi


if docker ps -a --format '{{.Names}}' | grep -wq postgres-db; then
    if [ "`docker inspect -f '{{.State.Running}}' redis-server`" != "true" ]; then
        echo "Starting existing postgres-db container..."
        docker start postgres-db
    else
        echo "redis-server container is already running."
    fi
else
    echo "Creating and starting redis-server container..."
    docker run --name postgres-db \
        -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
        -e POSTGRES_USERNAME=$POSTGRES_USERNAME \
        -e POSTGRES_DB=$POSTGRES_DB \
        -p 50432:50432 \
        -v postgres-data:/var/lib/postgresql/data \
        -d postgres
fi
