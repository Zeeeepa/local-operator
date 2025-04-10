from fastapi import Request, WebSocket

from local_operator.agents import AgentRegistry
from local_operator.config import ConfigManager
from local_operator.credentials import CredentialManager
from local_operator.jobs import JobManager
from local_operator.server.utils.websocket_manager import WebSocketManager


# Dependency functions to inject managers into route handlers
def get_credential_manager(request: Request) -> CredentialManager:
    """Get the credential manager from the application state."""
    return request.app.state.credential_manager


def get_config_manager(request: Request) -> ConfigManager:
    """Get the config manager from the application state."""
    return request.app.state.config_manager


def get_agent_registry(request: Request) -> AgentRegistry:
    """Get the agent registry from the application state."""
    return request.app.state.agent_registry


def get_job_manager(request: Request) -> JobManager:
    """Get the job manager from the application state."""
    return request.app.state.job_manager


def get_websocket_manager(request: Request) -> WebSocketManager:
    """Get the WebSocket manager from the application state."""
    return request.app.state.websocket_manager


async def get_websocket_manager_ws(websocket: WebSocket) -> WebSocketManager:
    """
    Get the WebSocket manager from the application state for WebSocket routes.

    This dependency is specifically designed for WebSocket routes where the
    Request object is not directly available.

    Args:
        websocket (WebSocket): The WebSocket connection.

    Returns:
        WebSocketManager: The WebSocket manager from the application state.
    """
    return websocket.app.state.websocket_manager
