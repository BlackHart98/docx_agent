#!/bin/bash

# if [ ! -d "env" ]; then 
#     echo "Creating python virtual environment..."

#     python -m venv env &&\ 
#     source env/bin/activate
# fi

# docker compose up --wait

# pip install -r requirements.txt && fastapi dev main.py

# Start postgres
sh bin/start_postgres.sh

# start redis server with the redis network
sh bin/start_redis.sh



