import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from urllib.parse import unquote

from app.storage import get_storage
from app.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.put("/local-upload/{key:path}")
async def local_upload(key: str, request: Request):
    """Handle local file uploads for testing."""
    try:
        storage = get_storage()
        
        # Get the raw body as bytes
        body = await request.body()
        
        # Save to temporary file first
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(body)
            temp_path = temp_file.name
        
        # Use storage's upload method
        success = storage.upload_file(temp_path, key)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        if success:
            return {"status": "success", "key": key}
        else:
            raise HTTPException(status_code=500, detail="Upload failed")
            
    except Exception as e:
        logger.error(f"Local upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/local-download/{key:path}")
async def local_download(key: str):
    """Handle local file downloads for testing."""
    try:
        storage = get_storage()
        
        # Get the file path
        if hasattr(storage, 'base_path'):
            file_path = os.path.join(storage.base_path, key)
            
            if os.path.exists(file_path):
                # Determine filename from key
                filename = os.path.basename(key)
                return FileResponse(
                    file_path,
                    filename=filename,
                    media_type="application/octet-stream"
                )
            else:
                raise HTTPException(status_code=404, detail="File not found")
        else:
            raise HTTPException(status_code=500, detail="Local storage not configured")
            
    except Exception as e:
        logger.error(f"Local download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))