from typing import List, Optional
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