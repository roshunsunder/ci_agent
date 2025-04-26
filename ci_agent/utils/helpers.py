from datetime import datetime
from ci_agent.dependencies import public_companies_table
import datetime
from datetime import datetime as dt
from boto3.dynamodb.conditions import Key, Attr

def retrieve_8K_documents(ent, retrieval_mode, date_range=None, latest_count=1):
    # Query for filings of type '10-K' for this company via the GSI.
    response = public_companies_table.query(
        IndexName='cik-filing_date-index',
        KeyConditionExpression=Key('cik').eq(str(ent.cik)),
        FilterExpression=Attr('filing_type').eq('8-K')
    )
    items = response.get('Items', [])
    
    if not items:
        return "No 8-K filings found."

    sep ="\n" + ("*" * 50) + "\n"

    # Sort filings by filing_date in descending order.
    sorted_filings = sorted(
        items,
        key=lambda item: dt.strptime(item['filing_date'], "%Y-%m-%d"),
        reverse=True
    )

    if retrieval_mode == 'latest':
        selected_filings = sorted_filings[:latest_count]
    elif retrieval_mode == 'date_range' and date_range:
        start_date = dt.strptime(date_range["start_date"], "%Y-%m-%d")
        end_date = dt.strptime(date_range["end_date"], "%Y-%m-%d")
        selected_filings = [
            item for item in sorted_filings 
            if start_date <= dt.strptime(item['filing_date'], "%Y-%m-%d") <= end_date
        ]
    else:
        raise ValueError("Invalid retrieval_mode or missing date_range")
    
    return "".join([
        f"##8-K Summary from {item['filing_date']}\n\n{item['summary']}{sep}"
        for item in selected_filings
    ])

def retrieve_10K_sections(ent, sections, retrieval_mode, date_range=None, latest_count=1):
    """
    Retrieve specific sections of 10-K summaries by date range or latest entries.
    
    Args:
        sections (list): List of sections to retrieve (e.g., ['Item 1 Business', 'Item 7 Management Discussion and Analysis']).
        retrieval_mode (str): Mode of retrieval, either 'date_range' or 'latest'.
        date_range (dict, optional): For 'date_range' mode, a dict with keys "start_date" and "end_date" (e.g., {"start_date": "2024-01-01", "end_date": "2024-12-31"}).
        latest_count (int, optional): Number of latest entries to retrieve if retrieval_mode is 'latest'.
    
    Returns:
        str: Formatted string containing the requested 10-K sections.
    """
    # Query for filings of type '10-K' for this company via the GSI.
    response = public_companies_table.query(
        IndexName='cik-filing_date-index',
        KeyConditionExpression=Key('cik').eq(str(ent.cik)),
        FilterExpression=Attr('filing_type').eq('10-K')
    )
    items = response.get('Items', [])
    
    if not items:
        return "No 10-K filings found."

    # Sort filings by filing_date in descending order.
    sorted_filings = sorted(
        items,
        key=lambda item: dt.strptime(item['filing_date'], "%Y-%m-%d"),
        reverse=True
    )
    
    if retrieval_mode == 'latest':
        selected_filings = sorted_filings[:latest_count]
    elif retrieval_mode == 'date_range' and date_range:
        start_date = dt.strptime(date_range["start_date"], "%Y-%m-%d")
        end_date = dt.strptime(date_range["end_date"], "%Y-%m-%d")
        selected_filings = [
            item for item in sorted_filings 
            if start_date <= dt.strptime(item['filing_date'], "%Y-%m-%d") <= end_date
        ]
    else:
        raise ValueError("Invalid retrieval_mode or missing date_range")
    
    sep = "\n" + ("*" * 50) + "\n"
    return _format_10K_sections(selected_filings, sections, sep)


def _format_10K_sections(filings, sections, sep):
    """
    Helper function to format the retrieved 10-K sections.
    
    Args:
        filings (list): List of filings (each is a dict with keys including 'filing_date' and 'summaries').
        sections (list): List of human‐readable section names to retrieve.
        sep (str): Separator string for formatting.
    
    Returns:
        str: Formatted string of the retrieved 10-K sections.
    """
    # Mapping of human‐readable section names to the keys used in the summaries.
    section_enums_mappings = {
        'Item 1 Business': 'Item 1',
        'Item 1A Risk Factors': 'Item 1A',
        'Item 2 Properties': 'Item 2',
        'Item 3 Legal Proceedings': 'Item 3',
        'Item 7 Management Discussion and Analysis': 'Item 7',
        'Item 7A Disclosures About Market Risk': 'Item 7A',
    }
    # Map provided sections to the keys present in summaries.
    section_keys = [section_enums_mappings.get(section) for section in sections if section in section_enums_mappings]

    results = []
    for filing in filings:
        filing_date = filing.get('filing_date', 'Unknown Date')
        summaries = filing.get('summaries', {})
        parts = [f"## 10-K Filing Date: {filing_date}"]
        for key in section_keys:
            if key in summaries:
                summary_text = summaries.get('key', 'Summary not available')
                parts.append(f"### {key}\n\n{summary_text}")
            else:
                parts.append(f"### {key}\n\nSection not found.")
        results.append(sep.join(parts))
    
    return sep.join(results)


def retrieve_10Q_sections(ent, sections, retrieval_mode, date_range=None, latest_count=1):
    """
    Retrieve specific sections of 10-Q summaries by date range or latest entries.
    
    Args:
        sections (list): List of sections to retrieve (e.g., ['Management Discussion', 'Risk Factors']).
        retrieval_mode (str): Mode of retrieval, either 'date_range' or 'latest'.
        date_range (dict, optional): For 'date_range' mode, a dict with "start_date" and "end_date".
        latest_count (int, optional): Number of latest entries to retrieve if retrieval_mode is 'latest'.
    
    Returns:
        str: Formatted string containing the requested 10-Q sections.
    """
    # Query for filings of type '10-Q' for this company via the GSI.
    response = public_companies_table.query(
        IndexName='cik-filing_date-index',
        KeyConditionExpression=Key('cik').eq(str(ent.cik)),
        FilterExpression=Attr('filing_type').eq('10-Q')
    )
    items = response.get('Items', [])
    
    if not items:
        return "No 10-Q filings found."
    
    # Sort filings by filing_date in descending order.
    sorted_filings = sorted(
        items,
        key=lambda item: dt.strptime(item['filing_date'], "%Y-%m-%d"),
        reverse=True
    )
    
    if retrieval_mode == 'latest':
        selected_filings = sorted_filings[:latest_count]
    elif retrieval_mode == 'date_range' and date_range:
        start_date = dt.strptime(date_range["start_date"], "%Y-%m-%d")
        end_date = dt.strptime(date_range["end_date"], "%Y-%m-%d")
        selected_filings = [
            item for item in sorted_filings
            if start_date <= dt.strptime(item['filing_date'], "%Y-%m-%d") <= end_date
        ]
    else:
        raise ValueError("Invalid retrieval_mode or missing date_range")
    
    sep = "\n" + ("*" * 50) + "\n"
    return _format_10Q_sections(selected_filings, sections, sep)


def _format_10Q_sections(filings, sections, sep):
    """
    Helper function to format the retrieved 10-Q sections.
    
    Args:
        filings (list): List of filings (each is a dict with keys including 'filing_date' and 'summaries').
        sections (list): List of sections to retrieve.
        sep (str): Separator string for formatting.
    
    Returns:
        str: Formatted string of the retrieved 10-Q sections.
    """
    tenq_section_enum_mappings = {
    'Item 1A Risk Factors': 'Item 1A',
    'Item 2 Management Discussion & Analysis of Financial Condition and Results of Operations' : 'Item 2',
    'Item 3 Disclosures About Market Risk' : 'Item 3'
    }

    section_keys = [tenq_section_enum_mappings.get(section) for section in sections if section in tenq_section_enum_mappings]
    results = []
    for filing in filings:
        filing_date = filing.get('filing_date', 'Unknown Date')
        summaries = filing.get('summaries', {})
        for key in section_keys:
            if key in summaries:
                # Look up the requested section in the summaries.
                section_content = summaries.get(key, 'No data available.')
                results.append(f"## Section: {key} from {filing_date}\n\n{section_content}{sep}")
    return "".join(results)

def retrieve_10K_financial_statement(ent, statement_type, retrieval_mode, date_range=None, latest_count=1):
    """
    Retrieve specific financial statements (balance sheet, income statement, or cash flow statement)
    from 10-K filings by date range or latest entries.
    
    Args:
        statement_type (str): The type of financial statement to retrieve 
                              ('balance sheet', 'income statement', or 'cash flow statement').
        retrieval_mode (str): Mode of retrieval, either 'date_range' or 'latest'.
        date_range (dict, optional): For 'date_range' mode, a dict with keys "start_date" and "end_date"
                                     in the format {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
        latest_count (int, optional): Number of latest entries to retrieve if retrieval_mode is 'latest'.
    
    Returns:
        str: Formatted string containing the requested financial statements.
    """
    # Query filings for this company of type "10-K" using the GSI.
    response = public_companies_table.query(
        IndexName='cik-filing_date-index',
        KeyConditionExpression=Key('cik').eq(str(ent.cik)),
        FilterExpression=Attr('filing_type').eq('10-K')
    )
    items = response.get('Items', [])
    if not items:
        return "No 10-K filings found."
    
    # Sort filings by filing_date in descending order.
    sorted_filings = sorted(
        items,
        key=lambda item: dt.strptime(item['filing_date'], "%Y-%m-%d"),
        reverse=True
    )
    
    # Filter by retrieval mode.
    if retrieval_mode == 'latest':
        selected_filings = sorted_filings[:latest_count]
    elif retrieval_mode == 'date_range' and date_range:
        start_date = dt.strptime(date_range["start_date"], "%Y-%m-%d")
        end_date = dt.strptime(date_range["end_date"], "%Y-%m-%d")
        selected_filings = [
            filing for filing in sorted_filings
            if start_date <= dt.strptime(filing['filing_date'], "%Y-%m-%d") <= end_date
        ]
    else:
        raise ValueError("Invalid retrieval_mode or missing date_range")
    
    sep = "\n" + ("*" * 50) + "\n"
    return _format_financials(selected_filings, statement_type, sep)


def retrieve_10Q_financial_statement(ent, statement_type, retrieval_mode, date_range=None, latest_count=1):
    """
    Retrieve specific financial statements (balance sheet, income statement, or cash flow statement)
    from 10-Q filings by date range or latest entries.
    
    Args:
        statement_type (str): The type of financial statement to retrieve 
                              ('balance sheet', 'income statement', or 'cash flow statement').
        retrieval_mode (str): Mode of retrieval, either 'date_range' or 'latest'.
        date_range (dict, optional): For 'date_range' mode, a dict with keys "start_date" and "end_date"
                                     in the format {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
        latest_count (int, optional): Number of latest entries to retrieve if retrieval_mode is 'latest'.
    
    Returns:
        str: Formatted string containing the requested financial statements.
    """
    # Query filings for this company of type "10-Q" using the GSI.
    response = public_companies_table.query(
        IndexName='cik-filing_date-index',
        KeyConditionExpression=Key('cik').eq(str(ent.cik)),
        FilterExpression=Attr('filing_type').eq('10-Q')
    )
    items = response.get('Items', [])
    if not items:
        return "No 10-Q filings found."
    
    # Sort filings by filing_date in descending order.
    sorted_filings = sorted(
        items,
        key=lambda item: dt.strptime(item['filing_date'], "%Y-%m-%d"),
        reverse=True
    )
    
    # Filter by retrieval mode.
    if retrieval_mode == 'latest':
        selected_filings = sorted_filings[:latest_count]
    elif retrieval_mode == 'date_range' and date_range:
        start_date = dt.strptime(date_range["start_date"], "%Y-%m-%d")
        end_date = dt.strptime(date_range["end_date"], "%Y-%m-%d")
        selected_filings = [
            filing for filing in sorted_filings
            if start_date <= dt.strptime(filing['filing_date'], "%Y-%m-%d") <= end_date
        ]
    else:
        raise ValueError("Invalid retrieval_mode or missing date_range")
    
    sep = "\n" + ("*" * 50) + "\n"
    return _format_financials(selected_filings, statement_type, sep)


def _format_financials(filings, statement_type, sep):
    """
    Helper function to format financial statement entries for display.
    
    Args:
        filings (list): List of filing items (each is a dict containing 'filing_date' and 'summaries').
        statement_type (str): The financial statement type (e.g., 'balance sheet').
        sep (str): Separator string for formatting.
    
    Returns:
        str: A formatted string that includes the financial statement data for each filing.
    """
    formatted_output = []
    for filing in filings:
        filing_date = filing.get('filing_date', 'Unknown Date')
        # In our new schema, financial statements are stored inside filing['summaries']['financials'].
        financials = filing.get('summaries', {}).get('financials', {})
        statement = financials.get(statement_type)
        if statement:
            formatted_output.append(
                f"## Financial Statement: {statement_type.title()} from {filing_date}\n\n{statement}{sep}"
            )
        else:
            formatted_output.append(
                f"## Financial Statement: {statement_type.title()} from {filing_date}\n\nNo data available.{sep}"
            )
    return "".join(formatted_output)