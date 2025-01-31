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

class AvailableInfo(BaseModel):
    """Information available on a particular entity"""
    info_dict: Dict[str, Tuple[str, str]]

class AgentConfig(BaseModel):
    """Information needed to instantiate an agent"""
    unique_id: str
    start_date: str
    data_sources : List[str]