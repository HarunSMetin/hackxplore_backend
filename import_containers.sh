#!/bin/bash
echo "Running manual container data import..."

# If inside Docker, run directly
if [ -f "/.dockerenv" ]; then
  cd /app
  python -m scripts.import_csv
else
  # If running outside Docker, use docker-compose exec
  docker-compose exec fastapi-app python -m scripts.import_csv
fi

echo "Import process completed." 