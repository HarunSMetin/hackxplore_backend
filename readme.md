# Container Occupancy Management Backend

This is an authentication-free backend application for container occupancy management, built with FastAPI and MySQL, and designed for integration with a Flutter frontend.

## Features
- No authentication (open API)
- CRUD operations for containers
- CO₂ emission estimation function
- Modular code structure
- Dockerized
- Auto-deploy via GitHub Actions
- OpenAPI/Swagger documentation (exportable for Flutter client generation)
- Automatic container data import from CSV

## Project Structure
- `main.py`: FastAPI entrypoint
- `routes/`: API route definitions
- `crud/`: CRUD logic
- `schemas/`: Pydantic schemas
- `models/`: SQLAlchemy models
- `database/`: DB connection and session
- `services/`: CO₂ computation logic
- `scripts/`: Data import scripts
- `.env.example`: Example environment variables
- `run.sh`: Run script
- `.github/workflows/deploy.yml`: CI/CD workflow

## Setup
1. Copy `.env.example` to `.env` and fill in your MySQL credentials.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run database migrations (if using Alembic):
   ```bash
   alembic upgrade head
   ```
4. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

## Data Import

The system is designed to automatically import container data from a CSV file during first setup when the containers table is empty. The CSV should be named `augmented_common_containers_with_types.csv` and placed in the project root directory.

Expected CSV format:
```
Name,Address,Latitude,Longitude,Date,Time,FillLevel_m3,Capacity_m3,Type
```

### Manual Import

To manually trigger data import at any time:

- **On Windows**: Run `import_containers.bat`
- **On Linux/Mac**: Run `./import_containers.sh` (make it executable first with `chmod +x import_containers.sh`)

## Docker
Build and run with Docker:
```bash
docker build -t container-backend .
# Ensure your .env file has correct MYSQL_HOST (e.g., host.docker.internal if MySQL runs on host)
docker run --env-file .env -p 8000:8000 container-backend
```

## Running with Docker Compose (Recommended for Development)

For a more integrated development setup, especially when running MySQL in Docker, use Docker Compose.

1.  **Ensure you have a `docker-compose.yml` file** (an example has been provided in the project root).
2.  **Configure your `.env` file:**
    *   The `docker-compose.yml` will set `MYSQL_HOST` to `mysql-db` (the service name of the MySQL container).
    *   Ensure `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DB` in your `.env` file match the `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` environment variables set for the `mysql-db` service in `docker-compose.yml`.
    *   Example `.env` for Docker Compose:
        ```env
        MYSQL_HOST=mysql-db
        MYSQL_PORT=3306
        MYSQL_USER=root
        MYSQL_PASSWORD=yourrootpassword
        MYSQL_DB=greenroad_db
        ```
3.  **Start the services:**
    ```bash
    docker-compose up --build
    ```
    This will start your FastAPI application and a MySQL container. The application will be available at `http://localhost:8000`.
    The MySQL database will be accessible from your host machine on port `3307` (as configured in `docker-compose.yml`) if you need to connect with a database GUI.

### Connecting FastAPI in Docker to MySQL

How your FastAPI container connects to MySQL depends on where MySQL is running:

*   **MySQL on the Host Machine (not in Docker):**
    *   Set `MYSQL_HOST=host.docker.internal` in your `.env` file (for Docker Desktop on Mac/Windows).
    *   For Linux, you might need to use your host's IP address (e.g., `172.17.0.1` or your LAN IP).
    *   Run your FastAPI container: `docker run --env-file .env -e MYSQL_HOST=host.docker.internal -p 8000:8000 container-backend`
*   **MySQL in another Docker Container (using Docker Compose - Recommended):**
    *   The `docker-compose.yml` handles this by setting `MYSQL_HOST` to the service name (e.g., `mysql-db`). Your FastAPI app then connects to `mysql-db:3306` internally within Docker's network.
*   **MySQL as a Cloud Service (AWS RDS, Google Cloud SQL, etc.):**
    *   Set `MYSQL_HOST` in your `.env` file to the endpoint URL provided by your cloud database provider.

## OpenAPI/Swagger for Flutter
- Access docs at `http://localhost:8000/docs`
- Export OpenAPI spec (for Flutter client generation):
  ```bash
  curl http://localhost:8000/openapi.json -o openapi.json
  # or YAML
  curl http://localhost:8000/openapi.yaml -o openapi.yaml
  ```

## Deployment
- On push to `main`, GitHub Actions will build and deploy using `run.sh` (simulate deployment).

## CO₂ Emission Estimation
- See `services/co2.py` for the estimation logic.

---
MIT License 