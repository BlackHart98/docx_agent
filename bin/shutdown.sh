#!/bin/bash

# Start postgres
sh bin/remove_postgres.sh

# start redis server with the redis network
sh bin/remove_redis.sh