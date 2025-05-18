import os
from dotenv import load_dotenv

load_dotenv()

# Database settings
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "yourrootpassword")
MYSQL_DB = os.getenv("MYSQL_DB", "greenroad_db")

# API settings
API_VERSION = "1.0.0"
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,https://your-frontend-domain.com"
).split(",")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "your-secret-api-key")