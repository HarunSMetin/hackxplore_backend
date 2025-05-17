from fastapi import FastAPI
from fastapi.routing import APIRoute
from routes import containers
import uvicorn
from fastapi.responses import RedirectResponse
from datetime import datetime

# Custom operationId for better client generation

def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}" if route.tags else route.name

app = FastAPI(generate_unique_id_function=custom_generate_unique_id)

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 