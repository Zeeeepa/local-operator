"""
Execution endpoints for the Local Operator API.

This module contains the FastAPI route handlers for execution-related endpoints,
providing detailed information about code execution.
"""

import logging
import os
import time
from typing import Dict, List, Optional

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

router = APIRouter(prefix="/v1/execution", tags=["Execution"])
logger = logging.getLogger("local_operator.server.routes.execution")


class ExecutionStats(BaseModel):
    """
    Model for execution statistics.
    """
    execution_time: float
    memory_usage: float
    cpu_usage: float


class CodeExecutionDetails(BaseModel):
    """
    Model for code execution details.
    """
    code: str
    result: Optional[str] = None
    error: Optional[str] = None
    stats: Optional[ExecutionStats] = None
    execution_id: str
    timestamp: float
    status: str  # "pending", "running", "completed", "failed"


class ExecutionHistory(BaseModel):
    """
    Model for execution history.
    """
    executions: List[CodeExecutionDetails]
    total_count: int


# In-memory storage for execution details (in a real implementation, this would be a database)
execution_history: Dict[str, CodeExecutionDetails] = {}


@router.get(
    "/history",
    response_model=CRUDResponse[ExecutionHistory],
    summary="Get execution history",
    description="Returns the history of code executions with detailed information.",
)
async def get_execution_history(
    limit: int = Query(10, description="Maximum number of executions to return"),
    offset: int = Query(0, description="Offset for pagination"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by execution status"),
    credential_manager: CredentialManager = Depends(get_credential_manager),
    config_manager: ConfigManager = Depends(get_config_manager),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """
    Get the history of code executions with detailed information.

    Args:
        limit: Maximum number of executions to return
        offset: Offset for pagination
        agent_id: Filter by agent ID
        status: Filter by execution status
        credential_manager: Dependency for managing credentials
        config_manager: Dependency for managing configuration
        agent_registry: Dependency for accessing agent registry

    Returns:
        A response containing the execution history
    """
    try:
        # Filter executions based on query parameters
        filtered_executions = list(execution_history.values())
        
        if agent_id:
            filtered_executions = [e for e in filtered_executions if e.agent_id == agent_id]
        
        if status:
            filtered_executions = [e for e in filtered_executions if e.status == status]
        
        # Sort by timestamp (newest first)
        filtered_executions.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Apply pagination
        paginated_executions = filtered_executions[offset:offset + limit]
        
        return CRUDResponse(
            status=200,
            message="Execution history retrieved successfully",
            result=ExecutionHistory(
                executions=paginated_executions,
                total_count=len(filtered_executions),
            ),
        )
    
    except Exception as e:
        logger.exception(f"Error retrieving execution history: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get(
    "/{execution_id}",
    response_model=CRUDResponse[CodeExecutionDetails],
    summary="Get execution details",
    description="Returns detailed information about a specific code execution.",
)
async def get_execution_details(
    execution_id: str,
    credential_manager: CredentialManager = Depends(get_credential_manager),
    config_manager: ConfigManager = Depends(get_config_manager),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
):
    """
    Get detailed information about a specific code execution.

    Args:
        execution_id: ID of the execution to retrieve
        credential_manager: Dependency for managing credentials
        config_manager: Dependency for managing configuration
        agent_registry: Dependency for accessing agent registry

    Returns:
        A response containing the execution details
    """
    try:
        if execution_id not in execution_history:
            raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")
        
        return CRUDResponse(
            status=200,
            message="Execution details retrieved successfully",
            result=execution_history[execution_id],
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions to preserve their status code and detail
        raise
    except Exception as e:
        logger.exception(f"Error retrieving execution details: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# Function to be called from other modules to record execution details
def record_execution(
    execution_id: str,
    code: str,
    result: Optional[str] = None,
    error: Optional[str] = None,
    status: str = "completed",
    agent_id: Optional[str] = None,
    execution_time: Optional[float] = None,
):
    """
    Record details about a code execution.

    Args:
        execution_id: Unique identifier for the execution
        code: The code that was executed
        result: The result of the execution (if successful)
        error: The error message (if failed)
        status: The status of the execution
        agent_id: The ID of the agent that executed the code
        execution_time: The time taken to execute the code (in seconds)
    """
    try:
        # Get system stats
        import psutil
        
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # in MB
        cpu_usage = process.cpu_percent(interval=0.1)
        
        # Create execution stats
        stats = ExecutionStats(
            execution_time=execution_time or 0.0,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
        )
        
        # Record execution details
        execution_history[execution_id] = CodeExecutionDetails(
            code=code,
            result=result,
            error=error,
            stats=stats,
            execution_id=execution_id,
            timestamp=time.time(),
            status=status,
            agent_id=agent_id,
        )
        
        logger.info(f"Recorded execution details for execution {execution_id}")
    
    except Exception as e:
        logger.exception(f"Error recording execution details: {e}")