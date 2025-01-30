from typing import Optional
from ci_agent.agent import Agent
from ci_agent.models.server_models import UserSession
from edgar import find
from edgar.entities import CompanySearchResults
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
router = APIRouter()

# Store active connections
active_connections = {}

async def verify_token(websocket: WebSocket) -> Optional[str]:
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

@router.websocket("/ask/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # Verify token before accepting connection
    ent = await verify_token(websocket)
    if not ent:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    try:
        await websocket.accept()

        streaming = False
        streaming_param = dict(websocket.query_params).get("stream", "false")
        if streaming_param.lower() == "true":
            streaming = True
        
        # Initialize your entity here using the verified token
        # ent = await initialize_entity(token)
        
        # Only store connection if authentication successful
        active_connections[user_id] = UserSession(
            websocket=websocket,
            agent=Agent(ent),
            streaming=streaming
        )
        
        try:
            user_session = active_connections[user_id]
            for _ in range(user_session.agent.MAX_TURNS):
                # Handle incoming messages
                data = await websocket.receive_text()
                # Process messages...
                user_session.agent.chat(message=data, streaming=streaming)
                # echo for now
                await websocket.send_text(f"You're {"not" if not streaming else ""} streaming!")
                await websocket.send_text(f"You said: {data}")
        except WebSocketDisconnect:
            # Clean up connection
            if user_id in active_connections:
                del active_connections[user_id]
                
    except Exception as e:
        # Handle any other errors
        print(e)
        if user_id in active_connections:
            del active_connections[user_id]
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)