from dotenv import load_dotenv
import os
import boto3
import warnings

# Create a DynamoDB client
load_dotenv("./.env")

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('REGION_NAME')
)

public_companies_table = dynamodb.Table('public_companies')
users_table = dynamodb.Table('users')
agents_table = dynamodb.Table('agents')

class Session:
    """
    Class to represent an individual chat session
    """
    def __init__(self, ws):
        self.websocket = ws
        self.agent = None
        self.streaming = True
    
    def set_agent(self, agent):
        self.agent = agent
    
    def get_agent(self):
        return self.agent

class ChatSessionManager:
    """
    Class built for managing the active chat sessions
    """
    def __init__(self):
        self.active_chats : dict[tuple[str, str], Session] = dict()
    
    def register_session(self, user_id, agent_id, ws):
        key = (user_id, agent_id)
        self.active_chats[key] = Session(ws)
        return 0
    
    def get_session(self, user_id, agent_id):
        key = (user_id, agent_id)
        if key not in self.active_chats:
            raise ValueError(f"No active session for ({user_id}, {agent_id}).")
        return self.active_chats.get(key)
    
    def assign_agent(self, user_id, agent_id, agent):
        key = (user_id, agent_id)
        if key not in self.active_chats:
            raise ValueError(f"No active session for ({user_id}, {agent_id}).")
        
        session = self.active_chats.get(key)

        if not session:
            raise ValueError("Empty session stored in cache. Something went wrong.")
        
        session.set_agent(agent)
    
    def deregister_session(self, user_id, agent_id):
        key = (user_id, agent_id)
        if key not in self.active_chats:
            warnings.warn("ATTEMPTING TO DELETE A SESSION THAT NO LONGER EXISTS")
            return
        del self.active_chats[key]

chat_session_manager = ChatSessionManager()
def gen_deps():
    return chat_session_manager

