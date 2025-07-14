#!/bin/bash
set -e

if docker ps -a --format '{{.Names}}' | grep -wq redis-server; then
    if [ "$(docker inspect -f '{{.State.Running}}' redis-server)" = "true" ]; then
        echo "Stopping redis-server container…"
        docker stop redis-server > /dev/null
    fi
    echo "Removing redis-server container…"
    docker rm redis-server > /dev/null
    echo "Removed redis-server container"
else
    echo "No redis-server container found."
fi

if docker network inspect redis-network >/dev/null 2>&1; then
    echo "Removing redis-network…"
    docker network rm redis-network > /dev/null
    echo "Removed redis-network"
else
    echo "No redis-network found."
fi