#!/bin/bash

# Start the Flask backend server
echo "Starting Premier League Predictor Backend..."
cd "$(dirname "$0")"
source venv/bin/activate
cd backend
python app.py



