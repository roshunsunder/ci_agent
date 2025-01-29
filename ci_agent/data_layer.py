"""
Principle behind this class is to act as an intermediary between data accessor functions / RAG
and the driving agent. 
"""
import os
from typing import List, Optional
from dotenv import load_dotenv
from edgar_data_modules import (
    get_10K_Item1_Business,
    get_10K_Item1A_Risk_Factors,
    get_10K_Item1B_Unresolved_Staff_Comments,
    get_10K_Item1C_Cybersecurity,
    get_10K_Item2_Properties,
    get_10K_Item3_Legal_Proceedings,
    get_10K_Item4_Mine_Safety_Disclosures,
    get_10K_Item5_Market,
    get_10K_Item6_Consolidated_Financial_Data,
    get_10K_Item7_Managements_Discussion_and_Analysis,
    get_10K_Item7A_Market_Risks,
    get_10K_Item8_Financial_Statements,
    get_10K_Item9_Changes_in_Accountants,
    get_10K_Item9A_Controls_and_Procedures,
    get_10K_Item9B_Other_Information,
    get_10K_Item10_Directors_Executive_Officers_and_Corporate_Governance,
    get_10K_Item11_Executive_Compensation,
    get_10K_Item12_Security_Ownership,
    get_10K_Item13_Related_Transactions_and_Director_Independence,
    get_10K_Item14_Principal_Accounting_Fees_and_Services,
    get_10K_Item15_Exhibits_and_Financial_Statement_Schedules,
    get_10K_balance_sheet,
    get_10K_income_statement,
    get_10K_cash_flow
)
from openai import OpenAI
from sentence_transformers import SentenceTransformer, util

DEFAULT_SYSTEM_PROMPT = """
You are an expert competitive analysis assistant. Your task is to analyze a information
(fincancial or otherwise) and extract key information that is relevant to the 
provided context and goal. Focus only on information that directly relates to 
the provided context and objective. Be concise but thorough in your analysis.
"""

class DataLayer:
    def __init__(self, llm_client, system_prompt: str = None):
        """Initializes Data"""
        self.llm_client = llm_client
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        if self.embedding_model is not None:
            print("Embedding Model Loaded") # TODO: change to logs
        
        self.tenk_functions = {
            'ITEM_01_BUSINESS':get_10K_Item1_Business,
            'ITEM_1A_RISK_FACTORS':get_10K_Item1A_Risk_Factors,
            'ITEM_1B_UNRESOLVED_STAFF_COMMENTS':get_10K_Item1B_Unresolved_Staff_Comments,
            'ITEM_1C_CYBERSECURITY':get_10K_Item1C_Cybersecurity,
            'ITEM_02_PROPERTIES':get_10K_Item2_Properties,
            'ITEM_03_LEGAL_PROCEEDINGS':get_10K_Item3_Legal_Proceedings,
            'ITEM_04_MINE_SAFETY_DISCLOSURES':get_10K_Item4_Mine_Safety_Disclosures,
            'ITEM_05_MARKET':get_10K_Item5_Market,
            'ITEM_06_CONSOLIDATED_FINANCIAL_DATA':get_10K_Item6_Consolidated_Financial_Data,
            'ITEM_07_MGMT_DISCUSSION_AND_ANALYSIS':get_10K_Item7_Managements_Discussion_and_Analysis,
            'ITEM_7A_MARKET_RISKS':get_10K_Item7A_Market_Risks,
            'ITEM_08_FINANCIAL_STATEMENTS':get_10K_Item8_Financial_Statements,
            'ITEM_09_CHANGES_IN_ACCOUNTANTS':get_10K_Item9_Changes_in_Accountants,
            'ITEM_9A_CONTROLS_AND_PROCEDURES': get_10K_Item9A_Controls_and_Procedures,
            'ITEM_9B_OTHER_INFORMATION': get_10K_Item9B_Other_Information,
            'ITEM_10_DIRECTORS_EXECUTIVE_OFFICERS_AND_GOVERNANCE': get_10K_Item10_Directors_Executive_Officers_and_Corporate_Governance,
            'ITEM_11_EXECUTIVE_COMPENSATION': get_10K_Item11_Executive_Compensation,
            'ITEM_12_SECURITY_OWNERSHIP': get_10K_Item12_Security_Ownership,
            'ITEM_13_RELATED_TRANSACTIONS_AND_DIRECTOR_INDEPENDENCE': get_10K_Item13_Related_Transactions_and_Director_Independence,
            'ITEM_14_PRINCIPAL_ACCOUNTING_FEES_AND_SERVICES': get_10K_Item14_Principal_Accounting_Fees_and_Services,
            'ITEM_15_EXHIBITS_AND_FINANCIAL_STATEMENT_SCHEDULES': get_10K_Item15_Exhibits_and_Financial_Statement_Schedules,
        }

        self.tenk_financial_functions = {
            'BALANCE_SHEET' : get_10K_balance_sheet,
            'INCOME_STATEMENT' : get_10K_income_statement,
            'CASH_FLOW' : get_10K_cash_flow
        }
    
    def _do_RAG(self, chunks: List[str], query: str, top_k:int = 1) -> List[str]:
        # Encode query and paragraphs
        query_embedding = self.embedding_model.encode(query, convert_to_tensor=True)
        chunk_embeddings = self.embedding_model.encode(chunks, convert_to_tensor=True)

        # Compute cosine similarity
        similarities = util.cos_sim(query_embedding, chunk_embeddings)

        top_results = similarities.argsort(descending=True)[0][:top_k]
        return [chunks[i] for i in top_results]
    
    def analyze_10K_section_helper(
            self,
            tenk,
            section_name: str,
            rag_query: Optional[str],
            max_tokens: Optional[int] = 500
    ):
        """Agent-facing helper function"""
        if section_name not in self.tenk_functions:
            raise ValueError(f"Unknown section: {section_name}")
        # Retrieve the section content
        section_content = self.tenk_functions[section_name](tenk)
        if rag_query is not None and len(rag_query) > 0:
            section_content = str(self._do_RAG(
                list(section_content.split('\n\n')),
                rag_query
            ))
        
        # TODO: Add LLM analysis

        return section_content
        
    def analyze_10K_finances_helper(
            self,
            tenk,
            section_name: str,
    ) -> str:
        """Agent-facing helper function"""
        if section_name not in self.tenk_financial_functions:
            raise ValueError(f"Unknown section: {section_name}")
        # Retrieve the section content
        section_content = self.tenk_financial_functions[section_name](tenk)
        return section_content

