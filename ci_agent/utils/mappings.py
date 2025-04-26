from ci_agent.utils.helpers import *

section_enums_mappings = {
    'Item 1 Business': 'Item 1',
    'Item 1A Risk Factors': 'Item 1A',
    'Item 2 Properties': 'Item 2',
    'Item 3 Legal Proceedings': 'Item 3',
    'Item 7 Management Discussion and Analysis': 'Item 7',
    'Item 7A Disclosures About Market Risk': 'Item 7A',
}

tenq_section_enum_mappings = {
    'Item 1A Risk Factors': 'Item 1A',
    'Item 2 Management Discussion & Analysis of Financial Condition and Results of Operations' : 'Item 2',
    'Item 3 Disclosures About Market Risk' : 'Item 3'
}

FUNCTION_MAPPINGS = {
    "retrieve_8K_documents": retrieve_8K_documents,
    "retrieve_10K_sections": retrieve_10K_sections,
    "retrieve_10K_financial_statement" : retrieve_10K_financial_statement,
    "retrieve_10Q_sections": retrieve_10Q_sections,
    "retrieve_10Q_financial_statement": retrieve_10Q_financial_statement
}