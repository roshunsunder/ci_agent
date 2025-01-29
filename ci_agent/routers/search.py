from typing import List
from fastapi import APIRouter, HTTPException, Query
from edgar import *
from ci_agent.models import SearchResult

# CORE LOGIC
set_identity("Roshun Sunder roshun.sunder@gmail.com")

# REVISE AFTER THIS
router = APIRouter()

@router.get("/search", response_model=List[SearchResult])
async def search_endpoint(query: str = Query(None)):
    """
    Search for companies in the SEC EDGAR database.
    Returns a list of matching companies with their basic information.
    """
    try:
        search_results = find(query)
        if len(search_results.results) == 1:
            res = search_results[0]
            return [SearchResult(
                name=res.display_name,
                cik=str(res.cik)
            )]
        
        if not search_results:
            return []
        
        results = []
        for index, row in search_results.results.iterrows():
            results.append(SearchResult(
                name=row['company'],
                cik=str(row['cik']),
            ))
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))