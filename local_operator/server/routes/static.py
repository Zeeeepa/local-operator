"""
Static file serving endpoints for the Local Operator API.

This module contains the FastAPI route handlers for serving static files.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter(tags=["Static"])
logger = logging.getLogger("local_operator.server.routes.static")

# Path to the static directory
STATIC_DIR = Path(__file__).parent.parent / "static"
HTML_DIR = STATIC_DIR / "html"


@router.get("/", response_class=HTMLResponse)
async def get_index():
    """
    Serve the index page.
    
    Returns:
        HTMLResponse: The index page HTML
    """
    try:
        # Try to load the index.html file, or fall back to default_index.html
        template_path = HTML_DIR / 'index.html' if (HTML_DIR / 'index.html').exists() else HTML_DIR / 'default_index.html'
        with open(template_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Index template not found')


@router.get("/documents", response_class=HTMLResponse)
async def get_document_upload_page():
    """
    Serve the document upload page.
    
    Returns:
        HTMLResponse: The document upload page HTML
    """
    try:
        with open(HTML_DIR / "document_upload.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document upload page not found")


@router.get("/static/{file_path:path}")
async def get_static_file(file_path: str):
    """
    Serve static files.
    
    Args:
        file_path: Path to the static file
        
    Returns:
        FileResponse: The requested file
    """
    file = STATIC_DIR / file_path
    if not file.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    return FileResponse(file)
