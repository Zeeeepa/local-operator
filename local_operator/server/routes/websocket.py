"""
WebSocket endpoints for the Local Operator API.

This module contains the FastAPI route handlers for WebSocket connections,
enabling real-time communication between the client and server.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from local_operator.agents import AgentRegistry
from local_operator.config import ConfigManager
from local_operator.credentials import CredentialManager
from local_operator.jobs import JobManager
from local_operator.server.dependencies import (
    get_agent_registry,
    get_config_manager,
    get_credential_manager,
    get_job_manager,
)
from local_operator.types import ConversationRecord

router = APIRouter(tags=["WebSocket"])
logger = logging.getLogger("local_operator.server.routes.websocket")


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages to connected clients.
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.job_subscribers: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Connect a client to the WebSocket server.

        Args:
            websocket: The WebSocket connection
            client_id: A unique identifier for the client
        """
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, client_id: str):
        """
        Disconnect a client from the WebSocket server.

        Args:
            websocket: The WebSocket connection
            client_id: A unique identifier for the client
        """
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        
        # Remove from job subscribers
        for job_id, subscribers in list(self.job_subscribers.items()):
            if websocket in subscribers:
                subscribers.remove(websocket)
            if not subscribers:
                del self.job_subscribers[job_id]
                
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Send a message to a specific client.

        Args:
            message: The message to send
            websocket: The WebSocket connection to send the message to
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: str, client_id: Optional[str] = None):
        """
        Broadcast a message to all connected clients or to a specific client.

        Args:
            message: The message to broadcast
            client_id: If provided, only broadcast to this client's connections
        """
        if client_id:
            if client_id in self.active_connections:
                disconnected = []
                for connection in self.active_connections[client_id]:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to client {client_id}: {e}")
                        disconnected.append(connection)
                
                # Clean up any disconnected clients
                for connection in disconnected:
                    self.active_connections[client_id].remove(connection)
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]
        else:
            # Broadcast to all clients
            all_connections = [
                conn for connections in self.active_connections.values() for conn in connections
            ]
            disconnected = []
            for connection in all_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to all clients: {e}")
                    disconnected.append(connection)
            
            # Clean up any disconnected clients
            for connection in disconnected:
                for client_id, connections in list(self.active_connections.items()):
                    if connection in connections:
                        connections.remove(connection)
                    if not connections:
                        del self.active_connections[client_id]

    def subscribe_to_job(self, job_id: str, websocket: WebSocket):
        """
        Subscribe a WebSocket connection to updates for a specific job.

        Args:
            job_id: The ID of the job to subscribe to
            websocket: The WebSocket connection to subscribe
        """
        if job_id not in self.job_subscribers:
            self.job_subscribers[job_id] = set()
        self.job_subscribers[job_id].add(websocket)
        logger.info(f"WebSocket subscribed to job {job_id}. Total subscribers: {len(self.job_subscribers[job_id])}")

    def unsubscribe_from_job(self, job_id: str, websocket: WebSocket):
        """
        Unsubscribe a WebSocket connection from updates for a specific job.

        Args:
            job_id: The ID of the job to unsubscribe from
            websocket: The WebSocket connection to unsubscribe
        """
        if job_id in self.job_subscribers and websocket in self.job_subscribers[job_id]:
            self.job_subscribers[job_id].remove(websocket)
            if not self.job_subscribers[job_id]:
                del self.job_subscribers[job_id]
            logger.info(f"WebSocket unsubscribed from job {job_id}")

    async def broadcast_job_update(self, job_id: str, message: str):
        """
        Broadcast a job update to all subscribers of that job.

        Args:
            job_id: The ID of the job that was updated
            message: The update message to broadcast
        """
        if job_id in self.job_subscribers:
            disconnected = []
            for connection in self.job_subscribers[job_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting job update for job {job_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up any disconnected subscribers
            for connection in disconnected:
                self.job_subscribers[job_id].remove(connection)
            if not self.job_subscribers[job_id]:
                del self.job_subscribers[job_id]


# Create a connection manager instance
manager = ConnectionManager()


class WebSocketCommand(BaseModel):
    """
    Model for WebSocket commands sent from the client.
    """
    command: str
    data: dict


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    credential_manager: CredentialManager = Depends(get_credential_manager),
    config_manager: ConfigManager = Depends(get_config_manager),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    WebSocket endpoint for real-time communication.

    Args:
        websocket: The WebSocket connection
        client_id: A unique identifier for the client
        credential_manager: Dependency for managing credentials
        config_manager: Dependency for managing configuration
        agent_registry: Dependency for accessing agent registry
        job_manager: Dependency for managing asynchronous jobs
    """
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                command_data = json.loads(data)
                command = WebSocketCommand(**command_data)
                
                if command.command == "ping":
                    # Simple ping-pong for connection health check
                    await manager.send_personal_message(
                        json.dumps({"event": "pong", "timestamp": command.data.get("timestamp")}),
                        websocket
                    )
                
                elif command.command == "subscribe_job":
                    # Subscribe to job updates
                    job_id = command.data.get("job_id")
                    if job_id:
                        manager.subscribe_to_job(job_id, websocket)
                        # Send initial job state
                        job = await job_manager.get_job(job_id)
                        if job:
                            await manager.send_personal_message(
                                json.dumps({
                                    "event": "job_update",
                                    "job_id": job_id,
                                    "status": job.status,
                                    "result": job.result,
                                    "error": job.error,
                                    "created_at": job.created_at.isoformat() if job.created_at else None,
                                    "started_at": job.started_at.isoformat() if job.started_at else None,
                                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                                }),
                                websocket
                            )
                
                elif command.command == "unsubscribe_job":
                    # Unsubscribe from job updates
                    job_id = command.data.get("job_id")
                    if job_id:
                        manager.unsubscribe_from_job(job_id, websocket)
                
                else:
                    # Unknown command
                    await manager.send_personal_message(
                        json.dumps({"event": "error", "message": f"Unknown command: {command.command}"}),
                        websocket
                    )
            
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"event": "error", "message": "Invalid JSON format"}),
                    websocket
                )
            except Exception as e:
                logger.exception(f"Error processing WebSocket message: {e}")
                await manager.send_personal_message(
                    json.dumps({"event": "error", "message": str(e)}),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.exception(f"Unexpected WebSocket error: {e}")
        manager.disconnect(websocket, client_id)


# Function to be called from other modules to broadcast job updates
async def broadcast_job_update(job_id: str, status: str, result: Optional[dict] = None, error: Optional[str] = None):
    """
    Broadcast a job update to all subscribers.

    Args:
        job_id: The ID of the job that was updated
        status: The new status of the job
        result: Optional result data
        error: Optional error message
    """
    message = json.dumps({
        "event": "job_update",
        "job_id": job_id,
        "status": status,
        "result": result,
        "error": error
    })
    await manager.broadcast_job_update(job_id, message)


# Function to broadcast chat updates
async def broadcast_chat_update(
    client_id: str,
    message_id: str,
    content: str,
    role: str,
    conversation: List[ConversationRecord],
    is_complete: bool = False
):
    """
    Broadcast a chat update to a specific client.

    Args:
        client_id: The client ID to broadcast to
        message_id: A unique identifier for the message
        content: The message content
        role: The role of the message sender (user, assistant, system)
        conversation: The updated conversation history
        is_complete: Whether this is the final update for this message
    """
    message = json.dumps({
        "event": "chat_update",
        "message_id": message_id,
        "content": content,
        "role": role,
        "is_complete": is_complete,
        "conversation": [
            {"role": msg.role, "content": msg.content, "files": msg.files}
            for msg in conversation
        ]
    })
    await manager.broadcast(message, client_id)