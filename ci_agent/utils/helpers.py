from datetime import datetime
from ci_agent.dependencies import public_companies_table

def retrieve_8K_documents(ent, retrieval_mode, date_range=None, latest_count=1):
    # Assuming `table` and `ent` are predefined elsewhere in your code.
    item = public_companies_table.get_item(Key={'cik': str(ent.cik)}).get('Item', {})
    sep ="\n" + ("*" * 50) + "\n"
    eightks = item['8-K']

    # Sort 8-K documents by date
    sorted_eightks = sorted(
        eightks.items(),
        key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'),
        reverse=True
    )

    if retrieval_mode == 'latest':
        # Return the latest `latest_count` documents
        return "".join([
            f"##8-K Summary from {item[0]}\n\n{item[1]['summary']}{sep}"
            for item in sorted_eightks[:latest_count]
        ])
    elif retrieval_mode == 'date_range' and date_range:
        # Parse the start_date and end_date from the date_range object
        start_date = datetime.strptime(date_range["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(date_range["end_date"], "%Y-%m-%d")

        # Filter documents within the date range
        filtered_eightks = [
            item for item in sorted_eightks
            if start_date <= datetime.strptime(item[0], '%Y-%m-%d') <= end_date
        ]

        # Return the filtered documents
        return "".join([
            f"##8-K Summary from {item[0]}\n\n{item[1]['summary']}{sep}"
            for item in filtered_eightks
        ])
    else:
        raise ValueError("Invalid retrieval_mode or missing date_range")

def retrieve_10K_sections(ent, sections, retrieval_mode, date_range=None, latest_count=1):
    """
    Retrieve specific sections of 10-K summaries by date range or latest entries.

    Args:
        sections (list): List of sections to retrieve (e.g., ['Item 1 Business', 'Item 7 Management Discussion and Analysis']).
        retrieval_mode (str): Mode of retrieval, either 'date_range' or 'latest'.
        date_range (dict, optional): Start and end date for the range if retrieval_mode is 'date_range'. Example: {"start_date": "2024-01-01", "end_date": "2024-12-31"}.
        latest_count (int, optional): Number of latest entries to retrieve if retrieval_mode is 'latest'.

    Returns:
        str: Formatted string containing the requested 10-K sections.
    """
    # Assuming `table` and `ent` are predefined elsewhere in your code.
    item = public_companies_table.get_item(Key={'cik': str(ent.cik)}).get('Item', {})
    sep = "\n" + ("*" * 50) + "\n"
    tenks = item.get('10-K', {})

    # Sort 10-K filings by date in descending order (most recent first)
    sorted_tenks = sorted(
        tenks.items(),
        key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'),  # Dates in database are 'YYYY-MM-DD'
        reverse=True
    )

    if retrieval_mode == 'latest':
        # Retrieve the latest `latest_count` entries
        latest_entries = sorted_tenks[:latest_count]
        return _format_10K_sections(latest_entries, sections, sep)

    elif retrieval_mode == 'date_range' and date_range:
        # Parse the start_date and end_date from the date_range object
        start_date = datetime.strptime(date_range["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(date_range["end_date"], "%Y-%m-%d")

        # Filter filings within the date range
        filtered_tenks = [
            item for item in sorted_tenks
            if start_date <= datetime.strptime(item[0], '%Y-%m-%d') <= end_date
        ]

        return _format_10K_sections(filtered_tenks, sections, sep)

    else:
        raise ValueError("Invalid retrieval_mode or missing date_range")


def _format_10K_sections(entries, sections, sep):
    """
    Helper function to format the retrieved 10-K sections.

    Args:
        entries (list): List of 10-K entries (date, content).
        sections (list): List of sections to retrieve.
        sep (str): Separator string for formatting.

    Returns:
        str: Formatted string of the retrieved 10-K sections.
    """
    section_enums_mappings = {
        'Item 1 Business': 'Item 1',
        'Item 1A Risk Factors': 'Item 1A',
        'Item 2 Properties': 'Item 2',
        'Item 3 Legal Proceedings': 'Item 3',
        'Item 7 Management Discusssion and Analaysis': 'Item 7',
        'Item 7A Disclosures About Market Risk': 'Item 7A',
    }

    # Map user-provided sections to their corresponding enums
    section_enums = [section_enums_mappings.get(section) for section in sections if section in section_enums_mappings]

    results = []
    for date, content in entries:
        result = [f"## 10-K Filing Date: {date}"]
        for section_enum in section_enums:
            if section_enum in content:
                summary = content[section_enum].get('summary', 'Summary not available')
                result.append(f"### {section_enum}\n\n{summary}")
            else:
                result.append(f"### {section_enum}\n\nSection not found.")
        results.append(sep.join(result))

    return sep.join(results)

def retrieve_10K_financial_statement(ent, statement_type, retrieval_mode, date_range=None, latest_count=1):
    """
    Retrieve specific financial statements (balance sheet, income statement, or cash flow statement)
    from 10-K filings by date range or latest entries.

    Args:
        statement_type (str): The type of financial statement to retrieve ('balance sheet', 'income statement', 'cash flow statement').
        retrieval_mode (str): Mode of retrieval, either 'date_range' or 'latest'.
        date_range (dict, optional): Start and end date for the range if retrieval_mode is 'date_range'.
                                     Example: {"start_date": "2024-01-01", "end_date": "2024-12-31"}.
        latest_count (int, optional): Number of latest entries to retrieve if retrieval_mode is 'latest'.

    Returns:
        str: Formatted string containing the requested financial statements.
    """
    # Assuming `table` and `ent` are predefined elsewhere in your code.
    item = public_companies_table.get_item(Key={'cik': str(ent.cik)}).get('Item', {})
    sep = "\n" + ("*" * 50) + "\n"
    tenks = item.get('10-K', {})

    # Sort 10-K filings by date in descending order (most recent first)
    sorted_tenks = sorted(
        tenks.items(),
        key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'),  # Dates in database are 'YYYY-MM-DD'
        reverse=True
    )

    def _format_financials(entries, statement_type):
        """
        Helper function to format financial statement entries for display.
        """
        formatted_output = []
        for date, data in entries:
            financials = data.get('financials', {})
            statement = financials.get(statement_type)
            if statement:
                formatted_output.append(
                    f"## Financial Statement: {statement_type.title()} from {date}\n\n{statement}{sep}"
                )
            else:
                formatted_output.append(
                    f"## Financial Statement: {statement_type.title()} from {date}\n\nNo data available.{sep}"
                )
        return "".join(formatted_output)

    if retrieval_mode == 'latest':
        # Retrieve the latest `latest_count` entries
        latest_entries = sorted_tenks[:latest_count]
        return _format_financials(latest_entries, statement_type)

    elif retrieval_mode == 'date_range' and date_range:
        # Parse the start_date and end_date from the date_range object
        start_date = datetime.strptime(date_range["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(date_range["end_date"], "%Y-%m-%d")

        # Filter filings within the date range
        filtered_tenks = [
            item for item in sorted_tenks
            if start_date <= datetime.strptime(item[0], '%Y-%m-%d') <= end_date
        ]

        return _format_financials(filtered_tenks, statement_type)

    else:
        raise ValueError("Invalid retrieval_mode or missing date_range")

def retrieve_10Q_sections(ent, sections, retrieval_mode, date_range=None, latest_count=1):
    """
    Retrieve specific sections of 10-Q summaries by date range or latest entries.

    Args:
        sections (list): List of sections to retrieve (e.g., ['Management Discussion', 'Risk Factors']).
        retrieval_mode (str): Mode of retrieval, either 'date_range' or 'latest'.
        date_range (dict, optional): Start and end date for the range if retrieval_mode is 'date_range'.
                                     Example: {"start_date": "2024-01-01", "end_date": "2024-12-31"}.
        latest_count (int, optional): Number of latest entries to retrieve if retrieval_mode is 'latest'.

    Returns:
        str: Formatted string containing the requested 10-Q sections.
    """
    # Assuming `table` and `ent` are predefined elsewhere in your code.
    item = public_companies_table.get_item(Key={'cik': str(ent.cik)}).get('Item', {})
    sep = "\n" + ("*" * 50) + "\n"
    tenqs = item.get('10-Q', {})

    # Sort 10-Q filings by date in descending order (most recent first)
    sorted_tenqs = sorted(
        tenqs.items(),
        key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'),  # Dates in database are 'YYYY-MM-DD'
        reverse=True
    )

    def _format_10Q_sections(entries, sections, sep):
        """
        Helper function to format 10-Q sections for display.
        """
        formatted_output = []
        for date, data in entries:
            for section in sections:
                section_content = data.get(section, {}).get('summary', 'No data available.')
                formatted_output.append(
                    f"## Section: {section} from {date}\n\n{section_content}{sep}"
                )
        return "".join(formatted_output)

    if retrieval_mode == 'latest':
        # Retrieve the latest `latest_count` entries
        latest_entries = sorted_tenqs[:latest_count]
        return _format_10Q_sections(latest_entries, sections, sep)

    elif retrieval_mode == 'date_range' and date_range:
        # Parse the start_date and end_date from the date_range object
        start_date = datetime.strptime(date_range["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(date_range["end_date"], "%Y-%m-%d")

        # Filter filings within the date range
        filtered_tenqs = [
            item for item in sorted_tenqs
            if start_date <= datetime.strptime(item[0], '%Y-%m-%d') <= end_date
        ]

        return _format_10Q_sections(filtered_tenqs, sections, sep)

    else:
        raise ValueError("Invalid retrieval_mode or missing date_range")

def retrieve_10Q_financial_statement(ent, statement_type, retrieval_mode, date_range=None, latest_count=1):
    """
    Retrieve specific financial statements (balance sheet, income statement, or cash flow statement)
    from 10-Q filings by date range or latest entries.

    Args:
        statement_type (str): The type of financial statement to retrieve ('balance sheet', 'income statement', 'cash flow statement').
        retrieval_mode (str): Mode of retrieval, either 'date_range' or 'latest'.
        date_range (dict, optional): Start and end date for the range if retrieval_mode is 'date_range'.
                                     Example: {"start_date": "2024-01-01", "end_date": "2024-12-31"}.
        latest_count (int, optional): Number of latest entries to retrieve if retrieval_mode is 'latest'.

    Returns:
        str: Formatted string containing the requested financial statements.
    """
    # Assuming `table` and `ent` are predefined elsewhere in your code.
    item = public_companies_table.get_item(Key={'cik': str(ent.cik)}).get('Item', {})
    sep = "\n" + ("*" * 50) + "\n"
    tenqs = item.get('10-Q', {})

    # Sort 10-Q filings by date in descending order (most recent first)
    sorted_tenqs = sorted(
        tenqs.items(),
        key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'),  # Dates in database are 'YYYY-MM-DD'
        reverse=True
    )

    def _format_financials(entries, statement_type):
        """
        Helper function to format financial statement entries for display.
        """
        formatted_output = []
        for date, data in entries:
            financials = data.get('financials', {})
            statement = financials.get(statement_type)
            if statement:
                formatted_output.append(
                    f"## Financial Statement: {statement_type.title()} from {date}\n\n{statement}{sep}"
                )
            else:
                formatted_output.append(
                    f"## Financial Statement: {statement_type.title()} from {date}\n\nNo data available.{sep}"
                )
        return "".join(formatted_output)

    if retrieval_mode == 'latest':
        # Retrieve the latest `latest_count` entries
        latest_entries = sorted_tenqs[:latest_count]
        return _format_financials(latest_entries, statement_type)

    elif retrieval_mode == 'date_range' and date_range:
        # Parse the start_date and end_date from the date_range object
        start_date = datetime.strptime(date_range["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(date_range["end_date"], "%Y-%m-%d")

        # Filter filings within the date range
        filtered_tenqs = [
            item for item in sorted_tenqs
            if start_date <= datetime.strptime(item[0], '%Y-%m-%d') <= end_date
        ]

        return _format_financials(filtered_tenqs, statement_type)

    else:
        raise ValueError("Invalid retrieval_mode or missing date_range")
