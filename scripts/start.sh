#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "Error: .env file not found in project root"
    exit 1
fi

mkdir -p data
docker compose up --build -d
echo "PM App started at http://localhost:8000"
