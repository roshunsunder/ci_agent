"""This is a set of functions for interacting with the SEC API"""

from typing import List
import requests
from rapidfuzz import process, fuzz


def fetch_cik_data() -> dict:
    """
    Fetch the SEC's mapping of tickers to CIKs.
    Returns a dictionary where keys are tickers and values contain CIKs and names.
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": "Roshun Sunder roshun.sunder@gmail.com"}
    response = requests.get(url, headers=headers, timeout=5)
    if response.status_code == 200:
        data = response.json()
        cik_data = {
            entry["title"]: {
                "cik": str(entry["cik_str"]).zfill(10),
                "ticker": entry["ticker"],
            }
            for entry in data.values()
        }
        return cik_data
    raise ConnectionError(f"Failed to fetch ticker data: {response.status_code}")


def search_company_by_name(search_term: str, cik_data: dict, limit=5) -> List[dict]:
    """
    Perform a fuzzy search on company names to find the closest matches.

    Args:
    - search_term (str): The user's search query.
    - cik_data (dict): Dictionary of ticker data from the SEC.
    - limit (int): Maximum number of results to return.

    Returns:
    - List of matched companies with their name and score.
    """
    search_term = search_term.lower()
    company_names = list(cik_data.keys())
    results = []

    for company_name in company_names:
        normalized = company_name.lower()
        if search_term == normalized:
            results.append(
                {
                    "name": company_name,
                    "_score": 101.00,
                    "cik": cik_data[company_name]["cik"],
                }
            )
        elif normalized.startswith(search_term):
            results.append(
                {
                    "name": company_name,
                    "_score": 100.00,
                    "cik": cik_data[company_name]["cik"],
                }
            )

    exact_names = [result["name"] for result in results]
    matches = process.extract(
        search_term, company_names, scorer=fuzz.token_ratio, limit=limit
    )
    transformed_matches = [
        {"name": match[0], "_score": match[1], "cik": cik_data[match[0]]["cik"]}
        for match in matches
    ]
    transformed_matches = (
        list(
            filter(lambda entry: entry["name"] not in exact_names, transformed_matches)
        )
        + results
    )
    transformed_matches.sort(key=lambda entry: entry["_score"], reverse=True)

    return transformed_matches
