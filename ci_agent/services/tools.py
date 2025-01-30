from ci_agent.utils.mappings import section_enums_mappings, tenq_section_enum_mappings

tools = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_8K_documents",
            "description": "Retrieve 8-K document summaries by date range or latest entries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "retrieval_mode": {
                        "type": "string",
                        "enum": ["date_range", "latest"],
                        "description": "Mode of retrieval: by date range or latest entries."
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date for the range (YYYY-MM-DD)."
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date for the range (YYYY-MM-DD)."
                            }
                        },
                        "required": ["start_date", "end_date"],
                        "description": "Date range for filtering documents. Required if retrieval_mode is 'date_range'."
                    },
                    "latest_count": {
                        "type": "integer",
                        "description": "Number of latest entries to retrieve. Required if retrieval_mode is 'latest'."
                    }
                },
                "required": ["document_type", "retrieval_mode"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_10K_sections",
            "description": "Retrieve specific sections of 10-K summaries by date range or latest entries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": list(section_enums_mappings.keys()),
                            "description": "Section of the 10-K to retrieve."
                        },
                        "description": "List of 10-K sections to retrieve."
                    },
                    "retrieval_mode": {
                        "type": "string",
                        "enum": ["date_range", "latest"],
                        "description": "Mode of retrieval: by date range or latest entries."
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date for the range (YYYY-MM-DD)."
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date for the range (YYYY-MM-DD)."
                            }
                        },
                        "required": ["start_date", "end_date"],
                        "description": "Date range for filtering sections. Required if retrieval_mode is 'date_range'."
                    },
                    "latest_count": {
                        "type": "integer",
                        "description": "Number of latest entries to retrieve. Required if retrieval_mode is 'latest'."
                    }
                },
                "required": ["sections", "retrieval_mode"],
                "additionalProperties": False
            }
        }
    },
        {
        "type": "function",
        "function": {
            "name": "retrieve_10K_financial_statement",
            "description": "Retrieve specific financial statements (balance sheet, income statement, or cash flow statement) from 10-K filings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "statement_type": {
                        "type": "string",
                        "enum": ["balance sheet", "income statement", "cash flow statement"],
                        "description": "The type of financial statement to retrieve."
                    },
                    "retrieval_mode": {
                        "type": "string",
                        "enum": ["date_range", "latest"],
                        "description": "Mode of retrieval: by date range or latest entries."
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date for the range (YYYY-MM-DD)."
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date for the range (YYYY-MM-DD)."
                            }
                        },
                        "required": ["start_date", "end_date"],
                        "description": "Date range for filtering financial statements. Required if retrieval_mode is 'date_range'."
                    },
                    "latest_count": {
                        "type": "integer",
                        "description": "Number of latest entries to retrieve. Required if retrieval_mode is 'latest'."
                    }
                },
                "required": ["statement_type", "retrieval_mode"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_10Q_sections",
            "description": "Retrieve specific sections of 10-Q summaries by date range or latest entries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": list(tenq_section_enum_mappings.keys()),
                            "description": "Section of the 10-Q to retrieve."
                        },
                        "description": "List of 10-Q sections to retrieve."
                    },
                    "retrieval_mode": {
                        "type": "string",
                        "enum": ["date_range", "latest"],
                        "description": "Mode of retrieval: by date range or latest entries."
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date for the range (YYYY-MM-DD)."
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date for the range (YYYY-MM-DD)."
                            }
                        },
                        "required": ["start_date", "end_date"],
                        "description": "Date range for filtering sections. Required if retrieval_mode is 'date_range'."
                    },
                    "latest_count": {
                        "type": "integer",
                        "description": "Number of latest entries to retrieve. Required if retrieval_mode is 'latest'."
                    }
                },
                "required": ["sections", "retrieval_mode"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_10Q_financial_statement",
            "description": "Retrieve specific financial statements (balance sheet, income statement, or cash flow statement) from 10-Q filings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "statement_type": {
                        "type": "string",
                        "enum": ["balance sheet", "income statement", "cash flow statement"],
                        "description": "The type of financial statement to retrieve."
                    },
                    "retrieval_mode": {
                        "type": "string",
                        "enum": ["date_range", "latest"],
                        "description": "Mode of retrieval: by date range or latest entries."
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date for the range (YYYY-MM-DD)."
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date for the range (YYYY-MM-DD)."
                            }
                        },
                        "required": ["start_date", "end_date"],
                        "description": "Date range for filtering financial statements. Required if retrieval_mode is 'date_range'."
                    },
                    "latest_count": {
                        "type": "integer",
                        "description": "Number of latest entries to retrieve. Required if retrieval_mode is 'latest'."
                    }
                },
                "required": ["statement_type", "retrieval_mode"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "perform_vector_search",
            "description": "Search for specific terms in document summaries or sections using vector similarity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "The term or phrase to search for."
                    },
                    "document_type": {
                        "type": "string",
                        "enum": ["10-K", "8-K"],
                        "description": "Type of document to search within. Leave empty to search across all types."
                    },
                    "retrieval_mode": {
                        "type": "string",
                        "enum": ["date_range", "latest"],
                        "description": "Mode of retrieval: by date range or latest entries."
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date for the range (YYYY-MM-DD)."
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date for the range (YYYY-MM-DD)."
                            }
                        },
                        "required": ["start_date", "end_date"],
                        "description": "Date range for filtering search results."
                    },
                    "latest_count": {
                        "type": "integer",
                        "description": "Number of latest entries to retrieve. Required if retrieval_mode is 'latest'."
                    }
                },
                "required": ["search_query"],
                "additionalProperties": False
            }
        }
    }
]

