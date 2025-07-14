#!/bin/bash
set -e

if docker ps -a --format '{{.Names}}' | grep -wq postgres-db; then
    if [ "$(docker inspect -f '{{.State.Running}}' postgres-db)" = "true" ]; then
        echo "Stopping postgres-db container…"
        docker stop postgres-db > /dev/null
    fi
    echo "Removing postgres-db container…"
    docker rm postgres-db > /dev/null
    echo "Removed postgres-db container"
else
    echo "No postgres-db container found."
fi