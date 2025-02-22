import json
import uuid
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import List
from fastapi import APIRouter, HTTPException, Query
from edgar import *
from ci_agent.models.server_models import AvailableInfo
from ci_agent.utils.constants import DATA_SOURCES
from ci_agent.agent import Agent
from ci_agent.dependencies import agents_table

# REVISE AFTER THIS
router = APIRouter()

@router.get("/selectcompany", response_model=AvailableInfo)
async def get_config(unique_id: str = Query(None)):
    """
    Take unique_id for company, return object encoding
    available information
    """
    # Right now just SEC companies
    ent = find(unique_id)
    if not ent:
        raise HTTPException(status_code=400, detail="This isn't currently a supported unique id.")
    response_dict = {}

    all_filings = ent.get_filings(form=DATA_SOURCES)
    for source in DATA_SOURCES:
        filings = all_filings.filter(form=source)
        latest = filings.latest()
        oldest_table = filings.tail(1)
        oldest = None
        if oldest_table:
            oldest = oldest_table[0]
        if not latest or not oldest:
            response_dict[source] = tuple()
            continue

        response_dict[source] = (
            str(oldest.filing_date), 
            str(latest.filing_date)
        )
    
    return AvailableInfo(info_dict=response_dict)

@router.post("/buildagent")
async def build_agent(unique_id:str = Query(None), user_id:str = Query(None)):
    if not unique_id:
        raise HTTPException(status_code=400, detail="Cannot build agent without unique id.")
    if not user_id:
        raise HTTPException(status_code=400, detail="Cannot build agent without user id.")
    
    # Hardcode to look one year back
    start_date = date.today() - relativedelta(years=1)
    ent = find(unique_id)
    # Hardcode all data sources
    agent = Agent(ent, start_date, DATA_SOURCES)
    agent.init_data()
    # Write to db
    agent_id = "a-" + str(uuid.uuid4())
    item = {
        "id" : agent_id,
        "time_created" : str(datetime.now()),
        "messages" : json.dumps(agent.messages),
        "start_date" : str(start_date),
        "ent_id" : unique_id,
        "user_id" : user_id
    }

    agents_table.put_item(Item=item)

    return {"agent_id" : agent_id}