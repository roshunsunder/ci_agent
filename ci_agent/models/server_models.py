from typing import Dict, List, Tuple
from ci_agent.agent import Agent
from fastapi import WebSocket
from pydantic import BaseModel, ConfigDict

class SearchResult(BaseModel):
    name: str
    cik: str

class UserSession(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    websocket: WebSocket
    agent: Agent
    streaming: bool

class LoginRequest(BaseModel):
    auth_provider_id: str  # e.g., Firebase UID
    provider_type: str  # e.g., "firebase", "github"
    email: str | None = None  # Optional, for new users
    name: str | None = None  # Optional, for new users

class AvailableInfo(BaseModel):
    """Information available on a particular entity"""
    info_dict: Dict[str, Tuple[str, str]]