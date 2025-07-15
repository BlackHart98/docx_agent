#!/bin/bash
source .env 

set -e

POSTGRES_CONTAINER=postgres-db

if ! docker image inspect postgres >/dev/null 2>&1; then
    echo "Pulling postgres 17 image..."
    docker pull postgres:17;
else
    echo "Postgres image already present."
fi


if docker ps -a --format '{{.Names}}' | grep -wq postgres-db; then
    if [ "`docker inspect -f '{{.State.Running}}' postgres-db`" != "true" ]; then
        echo "Starting existing postgres-db container..."
        docker start postgres-db
    else
        echo "postgres-db container is already running."
    fi
else
    echo "Creating and starting postgres-db container..."
    docker run --name postgres-db \
        -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
        -e POSTGRES_USERNAME=$POSTGRES_USERNAME \
        -e POSTGRES_DB=$POSTGRES_DB \
        -p 15432:5432 \
        -v postgres-data:/var/lib/postgresql/data \
        -d postgres
fi


until docker exec -i $POSTGRES_CONTAINER pg_isready -U postgres; do
  echo "Waiting for Postgres database to be ready..."
  sleep 10
done

# docker exec -i postgres-db export PGPASSWORD=$POSTGRES_PASSWORD

docker exec -i postgres-db psql -U $POSTGRES_USERNAME < ./schemas/create_schemas.sql