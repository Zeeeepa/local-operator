"""
UI endpoints for the Local Operator API.

This module contains the FastAPI route handlers for serving the UI files.
"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter(tags=["UI"])

# Get the path to the UI directory
ui_dir = Path(__file__).parent.parent.parent / "ui"

# Check if the UI directory exists
if not ui_dir.exists():
    ui_dir.mkdir(parents=True, exist_ok=True)


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def get_ui():
    """
    Serve the main UI page.

    Returns:
        HTMLResponse: The HTML content of the UI
    """
    index_path = ui_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    
    return FileResponse(index_path)


@router.get("/styles.css", include_in_schema=False)
async def get_styles():
    """
    Serve the CSS file for the UI.

    Returns:
        FileResponse: The CSS file
    """
    css_path = ui_dir / "styles.css"
    if not css_path.exists():
        raise HTTPException(status_code=404, detail="CSS file not found")
    
    return FileResponse(css_path, media_type="text/css")


@router.get("/app.js", include_in_schema=False)
async def get_app_js():
    """
    Serve the JavaScript file for the UI.

    Returns:
        FileResponse: The JavaScript file
    """
    js_path = ui_dir / "app.js"
    if not js_path.exists():
        raise HTTPException(status_code=404, detail="JavaScript file not found")
    
    return FileResponse(js_path, media_type="text/javascript")