from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from fastapi.security import APIKeyHeader
import os
from typing import Dict
import sys

# Add the scripts directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
from scripts.import_csv import import_data_from_csv

router = APIRouter()

# Simple API key auth for admin endpoints
API_KEY = os.getenv("ADMIN_API_KEY", "your-secret-api-key")
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key

# Function to run in background
def import_csv_task(filepath: str):
    try:
        import_data_from_csv(filepath)
    except Exception as e:
        print(f"Background CSV import failed: {e}")

@router.post("/import-csv", response_model=Dict[str, str])
async def trigger_csv_import(
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Trigger a CSV import from the predefined CSV file.
    This endpoint is protected by an API key.
    The import runs in the background to avoid blocking the API.
    """
    csv_file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "augmented_common_containers_with_types.csv"
    )
    
    if not os.path.exists(csv_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CSV file not found: {csv_file_path}"
        )
    
    # Add the task to run in the background
    background_tasks.add_task(import_csv_task, csv_file_path)
    
    return {"message": "CSV import started in the background"}

@router.post("/import-custom-csv", response_model=Dict[str, str])
async def trigger_custom_csv_import(
    csv_filename: str,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Trigger a CSV import from a custom CSV file (must be in the application directory).
    This endpoint is protected by an API key.
    The import runs in the background to avoid blocking the API.
    """
    # Security check: don't allow path traversal
    if "/" in csv_filename or "\\" in csv_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename. Filename must not contain path separators."
        )
    
    csv_file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        csv_filename
    )
    
    if not os.path.exists(csv_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CSV file not found: {csv_filename}"
        )
    
    # Add the task to run in the background
    background_tasks.add_task(import_csv_task, csv_file_path)
    
    return {"message": f"Import of {csv_filename} started in the background"}