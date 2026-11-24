#!/usr/bin/env bash
set -e

echo "Starting AI-Powered Website Link Analysis API..."
if [ -d "venv" ]; then
    source venv/bin/activate
fi

python run.py
