#!/bin/bash

if [ ! -d "env" ]; then 
    echo "Creating python virtual environment..."

    python -m venv env &&\ 
    source env/bin/activate
fi

pip install -r requirements.txt

# Start postgres
sh bin/start_postgres.sh

# start redis server with the redis network
sh bin/start_redis.sh

fastapi dev main.py &

sh bin/start_celery_workers.sh &
wait

