"""
System monitoring endpoints for the Local Operator API.

This module contains the FastAPI route handlers for system-related endpoints,
providing information about system resources.
"""

import logging
import os
import platform
import time
from typing import Dict, List, Optional

import psutil
from fastapi import APIRouter, Depends, HTTPException, Query
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

router = APIRouter(prefix="/v1/system", tags=["System"])
logger = logging.getLogger("local_operator.server.routes.system")


class SystemInfo(BaseModel):
    """
    Model for system information.
    """
    cpu_count: int
    cpu_usage: float
    memory_total: float
    memory_available: float
    memory_used: float
    memory_percent: float
    disk_total: float
    disk_used: float
    disk_free: float
    disk_percent: float
    platform: str
    python_version: str
    uptime: float


class ProcessInfo(BaseModel):
    """
    Model for process information.
    """
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    create_time: float
    username: str
    cmdline: List[str]


class SystemStats(BaseModel):
    """
    Model for system statistics.
    """
    system: SystemInfo
    process: ProcessInfo


@router.get(
    "/info",
    response_model=CRUDResponse[SystemStats],
    summary="Get system information",
    description="Returns information about the system resources.",
)
async def get_system_info(
    credential_manager: CredentialManager = Depends(get_credential_manager),
    config_manager: ConfigManager = Depends(get_config_manager),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """
    Get information about the system resources.

    Args:
        credential_manager: Dependency for managing credentials
        config_manager: Dependency for managing configuration
        agent_registry: Dependency for accessing agent registry

    Returns:
        A response containing system information
    """
    try:
        # Get system information
        cpu_count = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        memory = psutil.virtual_memory()
        memory_total = memory.total / (1024 * 1024 * 1024)  # GB
        memory_available = memory.available / (1024 * 1024 * 1024)  # GB
        memory_used = memory.used / (1024 * 1024 * 1024)  # GB
        memory_percent = memory.percent
        
        disk = psutil.disk_usage("/")
        disk_total = disk.total / (1024 * 1024 * 1024)  # GB
        disk_used = disk.used / (1024 * 1024 * 1024)  # GB
        disk_free = disk.free / (1024 * 1024 * 1024)  # GB
        disk_percent = disk.percent
        
        system_platform = platform.platform()
        python_version = platform.python_version()
        uptime = time.time() - psutil.boot_time()
        
        # Get process information
        process = psutil.Process(os.getpid())
        process_info = ProcessInfo(
            pid=process.pid,
            name=process.name(),
            status=process.status(),
            cpu_percent=process.cpu_percent(interval=0.1),
            memory_percent=process.memory_percent(),
            create_time=process.create_time(),
            username=process.username(),
            cmdline=process.cmdline(),
        )
        
        # Create system info
        system_info = SystemInfo(
            cpu_count=cpu_count,
            cpu_usage=cpu_usage,
            memory_total=memory_total,
            memory_available=memory_available,
            memory_used=memory_used,
            memory_percent=memory_percent,
            disk_total=disk_total,
            disk_used=disk_used,
            disk_free=disk_free,
            disk_percent=disk_percent,
            platform=system_platform,
            python_version=python_version,
            uptime=uptime,
        )
        
        return CRUDResponse(
            status=200,
            message="System information retrieved successfully",
            result=SystemStats(
                system=system_info,
                process=process_info,
            ),
        )
    
    except Exception as e:
        logger.exception(f"Error retrieving system information: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


class ResourceUsagePoint(BaseModel):
    """
    Model for a single point of resource usage data.
    """
    timestamp: float
    cpu_percent: float
    memory_percent: float


class ResourceUsageHistory(BaseModel):
    """
    Model for resource usage history.
    """
    data: List[ResourceUsagePoint]
    interval: float


# In-memory storage for resource usage history (in a real implementation, this would be a database)
resource_history: List[ResourceUsagePoint] = []
MAX_HISTORY_POINTS = 1000  # Maximum number of points to store


@router.get(
    "/usage",
    response_model=CRUDResponse[ResourceUsageHistory],
    summary="Get resource usage history",
    description="Returns the history of resource usage.",
)
async def get_resource_usage(
    limit: int = Query(60, description="Maximum number of data points to return"),
    credential_manager: CredentialManager = Depends(get_credential_manager),
    config_manager: ConfigManager = Depends(get_config_manager),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """
    Get the history of resource usage.

    Args:
        limit: Maximum number of data points to return
        credential_manager: Dependency for managing credentials
        config_manager: Dependency for managing configuration
        agent_registry: Dependency for accessing agent registry

    Returns:
        A response containing the resource usage history
    """
    try:
        # Record current resource usage
        current_usage = ResourceUsagePoint(
            timestamp=time.time(),
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
        )
        
        # Add to history
        resource_history.append(current_usage)
        
        # Trim history if it gets too large
        if len(resource_history) > MAX_HISTORY_POINTS:
            resource_history.pop(0)
        
        # Get the requested number of data points
        data_points = resource_history[-limit:] if limit < len(resource_history) else resource_history
        
        # Calculate the average interval between data points
        interval = 0
        if len(data_points) > 1:
            total_time = data_points[-1].timestamp - data_points[0].timestamp
            interval = total_time / (len(data_points) - 1) if len(data_points) > 1 else 0
        
        return CRUDResponse(
            status=200,
            message="Resource usage history retrieved successfully",
            result=ResourceUsageHistory(
                data=data_points,
                interval=interval,
            ),
        )
    
    except Exception as e:
        logger.exception(f"Error retrieving resource usage history: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post(
    "/usage/record",
    response_model=CRUDResponse,
    summary="Record current resource usage",
    description="Records the current resource usage for historical tracking.",
)
async def record_resource_usage(
    credential_manager: CredentialManager = Depends(get_credential_manager),
    config_manager: ConfigManager = Depends(get_config_manager),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """
    Record the current resource usage for historical tracking.

    Args:
        credential_manager: Dependency for managing credentials
        config_manager: Dependency for managing configuration
        agent_registry: Dependency for accessing agent registry

    Returns:
        A response indicating success or failure
    """
    try:
        # Record current resource usage
        current_usage = ResourceUsagePoint(
            timestamp=time.time(),
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
        )
        
        # Add to history
        resource_history.append(current_usage)
        
        # Trim history if it gets too large
        if len(resource_history) > MAX_HISTORY_POINTS:
            resource_history.pop(0)
        
        return CRUDResponse(
            status=200,
            message="Resource usage recorded successfully",
        )
    
    except Exception as e:
        logger.exception(f"Error recording resource usage: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")