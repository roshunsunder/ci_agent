from fastapi import APIRouter
import uuid
from ci_agent.models.server_models import LoginRequest
from ci_agent.utils.constants import DATA_SOURCES
from ci_agent.dependencies import users_table
from boto3.dynamodb.conditions import Key

# REVISE AFTER THIS
router = APIRouter()

@router.post("/login")
async def get_config_endpoint(request: LoginRequest):
    # Step 1: Check if user exists in DynamoDB
    response = users_table.query(
        IndexName="email-index",
        KeyConditionExpression=Key("email").eq(request.email)
    )

    items = response.get('Items', [])
    if items:
        # User exists, return internal user_id
        return {"id": items[0]["id"], "displayName": items[0]["name"], "new_user" : False}
    
    # Step 2: User does not exist, create a new entry
    new_user_id = str(uuid.uuid4())

    new_user = {
        "id": new_user_id,
        "auth_provider_id": request.auth_provider_id,
        "provider_type": request.provider_type,
        "email": request.email,
        "name": request.name
    }

    users_table.put_item(Item=new_user)

    return {"id": new_user_id, "displayName": new_user["name"], "new_user": True}