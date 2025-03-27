"""
File upload/download endpoints for the Local Operator API.

This module contains the FastAPI route handlers for file-related endpoints,
enabling file uploads and downloads.
"""

import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel

from local_operator.agents import AgentRegistry
from local_operator.config import ConfigManager
from local_operator.credentials import CredentialManager
from local_operator.server.dependencies import (
    get_agent_registry,
    get_config_manager,
    get_credential_manager,
)
from local_operator.server.models.schemas import CRUDResponse

router = APIRouter(prefix="/v1/files", tags=["Files"])
logger = logging.getLogger("local_operator.server.routes.files")


class FileInfo(BaseModel):
    """
    Model for file information.
    """
    filename: str
    path: str
    size: int
    content_type: str
    upload_time: float


class FileListResponse(BaseModel):
    """
    Model for file list response.
    """
    files: List[FileInfo]
    total_count: int


def get_upload_dir() -> Path:
    """
    Get the directory for file uploads.

    Returns:
        Path to the upload directory
    """
    # Create a directory for file uploads in the user's home directory
    upload_dir = Path.home() / "local-operator-home" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@router.post(
    "/upload",
    response_model=CRUDResponse[FileInfo],
    summary="Upload a file",
    description="Uploads a file to the server for use in code execution.",
)
async def upload_file(
    file: UploadFile = File(...),
    agent_id: Optional[str] = Form(None, description="Optional agent ID to associate with the file"),
    credential_manager: CredentialManager = Depends(get_credential_manager),
    config_manager: ConfigManager = Depends(get_config_manager),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """
    Upload a file to the server.

    Args:
        file: The file to upload
        agent_id: Optional agent ID to associate with the file
        credential_manager: Dependency for managing credentials
        config_manager: Dependency for managing configuration
        agent_registry: Dependency for accessing agent registry

    Returns:
        A response containing information about the uploaded file
    """
    try:
        # Generate a unique filename to avoid collisions
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1] if original_filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create the upload directory if it doesn't exist
        upload_dir = get_upload_dir()
        
        # Create a subdirectory for the agent if specified
        if agent_id:
            try:
                # Verify that the agent exists
                agent_registry.get_agent(agent_id)
                upload_dir = upload_dir / agent_id
                upload_dir.mkdir(parents=True, exist_ok=True)
            except KeyError:
                logger.warning(f"Agent {agent_id} not found, using default upload directory")
        
        # Save the file
        file_path = upload_dir / unique_filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create file info
        file_info = FileInfo(
            filename=original_filename,
            path=str(file_path),
            size=file_size,
            content_type=file.content_type or "application/octet-stream",
            upload_time=os.path.getctime(file_path),
        )
        
        return CRUDResponse(
            status=200,
            message="File uploaded successfully",
            result=file_info,
        )
    
    except Exception as e:
        logger.exception(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get(
    "/download/{filename}",
    response_class=FileResponse,
    summary="Download a file",
    description="Downloads a file from the server.",
)
async def download_file(
    filename: str,
    agent_id: Optional[str] = Query(None, description="Optional agent ID to look for the file"),
    credential_manager: CredentialManager = Depends(get_credential_manager),
    config_manager: ConfigManager = Depends(get_config_manager),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """
    Download a file from the server.

    Args:
        filename: The name of the file to download
        agent_id: Optional agent ID to look for the file
        credential_manager: Dependency for managing credentials
        config_manager: Dependency for managing configuration
        agent_registry: Dependency for accessing agent registry

    Returns:
        The file as a response
    """
    try:
        # Get the upload directory
        upload_dir = get_upload_dir()
        
        # Check if the file exists in the agent's directory if specified
        if agent_id:
            agent_dir = upload_dir / agent_id
            if agent_dir.exists():
                for file_path in agent_dir.iterdir():
                    if file_path.name == filename:
                        return FileResponse(
                            path=file_path,
                            filename=filename,
                            media_type="application/octet-stream",
                        )
        
        # Check if the file exists in the main upload directory
        for file_path in upload_dir.iterdir():
            if file_path.name == filename:
                return FileResponse(
                    path=file_path,
                    filename=filename,
                    media_type="application/octet-stream",
                )
        
        # File not found
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    except HTTPException:
        # Re-raise HTTP exceptions to preserve their status code and detail
        raise
    except Exception as e:
        logger.exception(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get(
    "/list",
    response_model=CRUDResponse[FileListResponse],
    summary="List uploaded files",
    description="Lists all files uploaded to the server.",
)
async def list_files(
    agent_id: Optional[str] = Query(None, description="Optional agent ID to filter files"),
    limit: int = Query(10, description="Maximum number of files to return"),
    offset: int = Query(0, description="Offset for pagination"),
    credential_manager: CredentialManager = Depends(get_credential_manager),
    config_manager: ConfigManager = Depends(get_config_manager),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """
    List all files uploaded to the server.

    Args:
        agent_id: Optional agent ID to filter files
        limit: Maximum number of files to return
        offset: Offset for pagination
        credential_manager: Dependency for managing credentials
        config_manager: Dependency for managing configuration
        agent_registry: Dependency for accessing agent registry

    Returns:
        A response containing the list of files
    """
    try:
        # Get the upload directory
        upload_dir = get_upload_dir()
        
        # Get all files
        files = []
        
        # If agent_id is specified, only look in that agent's directory
        if agent_id:
            agent_dir = upload_dir / agent_id
            if agent_dir.exists():
                for file_path in agent_dir.iterdir():
                    if file_path.is_file():
                        files.append(FileInfo(
                            filename=file_path.name,
                            path=str(file_path),
                            size=os.path.getsize(file_path),
                            content_type="application/octet-stream",  # Default content type
                            upload_time=os.path.getctime(file_path),
                        ))
        else:
            # Look in the main upload directory
            for file_path in upload_dir.iterdir():
                if file_path.is_file():
                    files.append(FileInfo(
                        filename=file_path.name,
                        path=str(file_path),
                        size=os.path.getsize(file_path),
                        content_type="application/octet-stream",  # Default content type
                        upload_time=os.path.getctime(file_path),
                    ))
            
            # Look in all agent directories
            for agent_dir in upload_dir.iterdir():
                if agent_dir.is_dir():
                    for file_path in agent_dir.iterdir():
                        if file_path.is_file():
                            files.append(FileInfo(
                                filename=file_path.name,
                                path=str(file_path),
                                size=os.path.getsize(file_path),
                                content_type="application/octet-stream",  # Default content type
                                upload_time=os.path.getctime(file_path),
                            ))
        
        # Sort files by upload time (newest first)
        files.sort(key=lambda f: f.upload_time, reverse=True)
        
        # Apply pagination
        paginated_files = files[offset:offset + limit]
        
        return CRUDResponse(
            status=200,
            message="Files listed successfully",
            result=FileListResponse(
                files=paginated_files,
                total_count=len(files),
            ),
        )
    
    except Exception as e:
        logger.exception(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.delete(
    "/{filename}",
    response_model=CRUDResponse,
    summary="Delete a file",
    description="Deletes a file from the server.",
)
async def delete_file(
    filename: str,
    agent_id: Optional[str] = Query(None, description="Optional agent ID to look for the file"),
    credential_manager: CredentialManager = Depends(get_credential_manager),
    config_manager: ConfigManager = Depends(get_config_manager),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """
    Delete a file from the server.

    Args:
        filename: The name of the file to delete
        agent_id: Optional agent ID to look for the file
        credential_manager: Dependency for managing credentials
        config_manager: Dependency for managing configuration
        agent_registry: Dependency for accessing agent registry

    Returns:
        A response indicating success or failure
    """
    try:
        # Get the upload directory
        upload_dir = get_upload_dir()
        
        # Check if the file exists in the agent's directory if specified
        if agent_id:
            agent_dir = upload_dir / agent_id
            if agent_dir.exists():
                for file_path in agent_dir.iterdir():
                    if file_path.name == filename:
                        os.remove(file_path)
                        return CRUDResponse(
                            status=200,
                            message=f"File {filename} deleted successfully",
                        )
        
        # Check if the file exists in the main upload directory
        for file_path in upload_dir.iterdir():
            if file_path.name == filename:
                os.remove(file_path)
                return CRUDResponse(
                    status=200,
                    message=f"File {filename} deleted successfully",
                )
        
        # File not found
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    except HTTPException:
        # Re-raise HTTP exceptions to preserve their status code and detail
        raise
    except Exception as e:
        logger.exception(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")