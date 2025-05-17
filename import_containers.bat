@echo off
echo Running manual container data import...

docker-compose exec fastapi-app python -m scripts.import_csv

echo Import process completed.
pause 