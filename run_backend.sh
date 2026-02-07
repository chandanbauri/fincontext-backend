#!/bin/bash
cd /Users/chandanbauri/work/personal/hackathon/fincontext/backend
source venv/bin/activate
export ELASTIC_CLOUD_ID=$(grep ELASTIC_CLOUD_ID .env | cut -d '=' -f2)
export ELASTIC_API_KEY=$(grep ELASTIC_API_KEY .env | cut -d '=' -f2)
python3 main.py
