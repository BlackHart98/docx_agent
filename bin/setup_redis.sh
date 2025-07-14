#!/bin/bash
set -e
if ! docker image inspect redis >/dev/null 2>&1; then
    echo "Pulling redis image..."
    docker pull redis;
else
    echo "Redis image already present."
fi


if ! docker network inspect redis-network >/dev/null 2>&1; then
    echo "Creating redis-network..."
    docker network create --subnet=192.168.1.0/24 redis-network
else
    echo "Network redis-network already exists."
fi


if docker ps -a --format '{{.Names}}' | grep -wq redis-server; then
    if [ "`docker inspect -f '{{.State.Running}}' redis-server`" != "true" ]; then
        echo "Starting existing redis-server container..."
        docker start redis-server
    else
        echo "redis-server container is already running."
    fi
else
    echo "Creating and starting redis-server container..."
    docker run --name redis-server --net redis-network --ip 192.168.1.100 -p 6379:6379 -d redis
fi