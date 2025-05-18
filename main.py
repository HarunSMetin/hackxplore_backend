from fastapi import FastAPI
from fastapi.routing import APIRoute
from routes import containers, truck, admin  # Add the admin import
import uvicorn
from fastapi.responses import RedirectResponse
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import os

# Custom operationId for better client generation

def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}" if route.tags else route.name

app = FastAPI(generate_unique_id_function=custom_generate_unique_id)

# Get allowed origins from environment variable
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,https://your-frontend-domain.com"
).split(",")

# Add CORS middleware with environment-based configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Root endpoint that redirects to the API docs
@app.get("/", tags=["root"])
def root():
    return RedirectResponse(url="/docs")

# Health check endpoint
@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Include routers
app.include_router(containers.router, prefix="/containers", tags=["containers"])
app.include_router(truck.router, tags=["trucks"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])  # Add the admin router

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)