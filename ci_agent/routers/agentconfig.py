from typing import List
from fastapi import APIRouter, HTTPException, Query
from edgar import *
from ci_agent.models.server_models import AvailableInfo
from ci_agent.utils.constants import DATA_SOURCES

# REVISE AFTER THIS
router = APIRouter()

@router.get("/selectcompany", response_model=AvailableInfo)
async def get_config_endpoint(unique_id: str = Query(None)):
    """
    Take unique_id for company, return object encoding
    available information
    """
    # Right now just SEC companies
    ent = find(unique_id)
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