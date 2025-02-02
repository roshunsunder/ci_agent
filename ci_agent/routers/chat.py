from datetime import date, datetime
from typing import Optional
from ci_agent.agent import Agent
from ci_agent.models.server_models import UserSession
from ci_agent.utils.constants import DATA_SOURCES
from edgar import find
from edgar.entities import CompanySearchResults
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
router = APIRouter()

# Store active connections
active_connections = {}

async def verify(websocket: WebSocket) -> Optional[str]:
    """Verify the authentication token from the connection request."""
    try:
        # Get headers from the connection request
        headers = dict(websocket.headers)
        # Get query parameters
        query_params = dict(websocket.query_params)
        
        # Auth
        # token = (
        #     headers.get('authorization', '').replace('Bearer ', '') or
        #     query_params.get('token') or
        #     websocket.cookies.get('token')
        # )
        
        ent = find(query_params.get('unique_id'))
        if not ent or isinstance(ent, CompanySearchResults) :
            return None
            
        # Add your token validation logic here
        # For example, verify against your database or decode a JWT
        # Return None if validation fails
        
        return ent
    except Exception:
        return None

def verify_date(date_str: str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def verify_sources(data_sources: list[str]):
    return (
        not data_sources 
        or not any(item not in DATA_SOURCES for item in data_sources)
    )

@router.websocket("/ask/{user_id}")
async def websocket_endpoint(
        websocket: WebSocket, 
        user_id: str, 
        data_sources: list[str] = Query([]),
        start_date: str = Query(""),
        stream: bool = Query(False)
    ):
    # Verify before accepting connection
    ent = await verify(websocket)
    valid_date = verify_date(start_date)
    valid_sources = verify_sources(data_sources)

    if (
        not ent
        or not valid_sources
        or not valid_date
    ):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        await websocket.accept()
        
        # Only store connection if authentication successful
        active_connections[user_id] = UserSession(
            websocket=websocket,
            agent=Agent(ent, start_date, data_sources),
            streaming=stream
        )
        
        try:
            user_session = active_connections[user_id]
            user_session.agent.init_data()
            for _ in range(user_session.agent.MAX_CHAT_TURNS):
                # Handle incoming messages
                data = await websocket.receive_text()
                # Process messages...
                if stream:
                    stream = user_session.agent.chat(message=data, streaming=stream)
                    for chunk in stream:
                        if chunk:
                            await websocket.send_text(chunk)
                else:
                    response = user_session.agent.chat(message=data, streaming=stream)
                    await websocket.send_text(response)
        except WebSocketDisconnect:
            # Clean up connection
            if user_id in active_connections:
                del active_connections[user_id]
                
    except Exception as e:
        # Handle any other errors
        if user_id in active_connections:
            del active_connections[user_id]
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        print(e)