#!/bin/bash

# Apply database migrations
echo "Applying database migrations..."
python message_sender/manage.py migrate

# Start server
echo "Starting server..."
python message_sender/manage.py runserver 0.0.0.0:8000
