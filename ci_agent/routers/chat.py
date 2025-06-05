import json
from ci_agent.agent import Agent
from ci_agent.dependencies import agents_table
from ci_agent.utils.constants import DATA_SOURCES
from ci_agent.dependencies import gen_deps
from edgar import find
from edgar.entities import CompanySearchResults
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from botocore.exceptions import ClientError
router = APIRouter()

@router.websocket("/ask/{agent_id}")
async def websocket_endpoint(
        websocket: WebSocket,
        agent_id: str,
        user_id: str,
        chat_session_manager = Depends(gen_deps)
    ):
    stream = True # Harcode all clients to use streaming

    # Attempt to retrieve agent information
    try:
        response = agents_table.get_item(Key={
            'id': agent_id,
            'user_id': user_id
        })
        agent_info = response.get('Item')
        ent = find(agent_info['ent_id'])
        start_date = agent_info['start_date']
        data_sources = agent_info['data_sources']
        if not agent_info:
            print(f"No item found with id: {agent_id}")
            return None
    except ClientError as e:
        print(f"Error getting item: {e.response['Error']['Message']}")
        return None
    
    try:
        # Only store connection if authentication successful
        chat_session_manager.register_session(
            user_id,
            agent_id,
            websocket
        )

        chat_session_manager.assign_agent(
            user_id,
            agent_id,
            Agent(ent, start_date, data_sources)
        )
        
        try:
            await websocket.accept()
            user_session = chat_session_manager.get_session(user_id, agent_id)
            agent = user_session.agent

            # Check for missing data
            missing_data = agent.check_for_missing_data()
            if missing_data:
                payload = [
                    {
                    "source" : entry["source"], 
                    "filing_date": entry["filing_date"]
                    }
                for entry in missing_data]

                await websocket.send_json({
                    "MESSAGE_TYPE" : "SERVER_MESSAGE",
                    "MESSAGE_SUBTYPE": "MISSING_DATA",
                    "PAYLOAD": payload
                })
                
                fill_decision = await websocket.receive_json()
                if fill_decision["MESSAGE_TYPE"] != "USER_EVENT":
                    # Log error
                    print(f"Malformed user message received from user {user_id}")
                    return
                elif fill_decision["MESSAGE_SUBTYPE"] == "FILL_DATA":
                    print(f"Filling missing data for agent {agent_id}")
                    agent.fill_missing_data(missing_data)
                elif fill_decision["MESSAGE_SUBTYPE"] != "SKIP_FILL_DATA":
                    print(f"Unrecognized message subtype from user {user_id}")
                    
            # Once finished, send ready
            await websocket.send_json({
                "MESSAGE_TYPE": "AGENT_STATUS",
                "MESSAGE_SUBTYPE": "READY",
                "PAYLOAD": "" # This should be the agent message history
            })   
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
            chat_session_manager.deregister_session(
                user_id,
                agent_id
            )
                
    except Exception as e:
        # Handle any other errors
        chat_session_manager.deregister_session(
                user_id,
                agent_id
            )
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        raise e