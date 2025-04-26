from typing import List, Optional
from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    information_needed: List[str] = Field(..., description="List of pieces of information needed to answer the user question, IN ORDER. If the user's question doesn't requre outside information (for instance if you already have the information in your context history) then you must leave this empty. You must be specific and explicit with respect to the source of information you are requesting.")