"""Agent that handles the ReACT CoT"""
import os
import json
import logging
from logging.handlers import RotatingFileHandler
import tiktoken
from openai import OpenAI
from data_layer import DataLayer
from edgar_data_modules import (
    config_and_set_company,
    get_latest_10K
)
from dotenv import load_dotenv

load_dotenv()


MAX_STEPS = 5

def num_tokens_from_string(string: str, model_name: str) -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def setup_logger(name: str, log_file: str = 'react_agent.log', level=logging.INFO):
    """Configure logger with both file and console handlers"""
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    # File handler (rotating to keep log size manageable)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

class ReActAgent:
    def __init__(self, company_ticker_or_cik, data_analysis_client):
        self.logger = setup_logger(self.__class__.__name__)
        self.llm_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.company = config_and_set_company(company_ticker_or_cik)
        if self.company is None:
            self.logger.error(f"Company not found for ticker/CIK: {company_ticker_or_cik}")
            raise ValueError(f"Couldn't find a company for ticker/CIK: {company_ticker_or_cik}")
        self.tools =[
            {
                "type": "function",
                "function": {
                    "name": "get_10K_section",
                    "description": "Retrieve and filter text from a specific section of the company's 10K filing. Use this to extract relevant information about the company.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "section": {
                                "type": "string",
                                "enum" : ['ITEM_01_BUSINESS', 'ITEM_1A_RISK_FACTORS', 'ITEM_1B_UNRESOLVED_STAFF_COMMENTS', 'ITEM_1C_CYBERSECURITY', 'ITEM_02_PROPERTIES', 'ITEM_03_LEGAL_PROCEEDINGS', 'ITEM_04_MINE_SAFETY_DISCLOSURES', 'ITEM_05_MARKET', 'ITEM_06_CONSOLIDATED_FINANCIAL_DATA', 'ITEM_07_MGMT_DISCUSSION_AND_ANALYSIS', 'ITEM_7A_MARKET_RISKS', 'ITEM_09_CHANGES_IN_ACCOUNTANTS', 'ITEM_9A_CONTROLS_AND_PROCEDURES', 'ITEM_9B_OTHER_INFORMATION', 'ITEM_10_DIRECTORS_EXECUTIVE_OFFICERS_AND_GOVERNANCE', 'ITEM_11_EXECUTIVE_COMPENSATION', 'ITEM_12_SECURITY_OWNERSHIP', 'ITEM_13_RELATED_TRANSACTIONS_AND_DIRECTOR_INDEPENDENCE', 'ITEM_14_PRINCIPAL_ACCOUNTING_FEES_AND_SERVICES'],
                                "description" : "The specific section of the 10K to retrieve, such as ITEM_1A_RISK_FACTORS for risk factors or ITEM_07_MGMT_DISCUSSION_AND_ANALYSIS for management discussion. Use these enums to target a specific area of the filing."
                            },
                            "rag_query" : {
                                "type": "string",
                                "description" : "A keyword or phrase to filter content within the specified section. For example, if analyzing ITEM_1A_RISK_FACTORS, you might use 'regulatory risk' to find paragraphs discussing regulatory challenges."
                            }
                        },
                    },
                    "required" : ["section", "rag_query"]
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_10K_financial_statement",
                    "description": "Retrieve a financial statement from the 10K filing in markdown format. Use this when information is needed from the balance sheet, income statement, or cash flow statement.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "statement": {
                                "type": "string",
                                "enum" : ['BALANCE_SHEET', 'INCOME_STATEMENT', 'CASH_FLOW'],
                                "description" : "The specific financial statement from the 10K to retrieve"
                            }
                        },
                    },
                    "required" : ["statement"]
                }
            },
            {
                "type" : "function",
                "function" : {
                    "name" : "finish",
                    "description" : "Conclude the reasoning process and provide the final answer to the question. Use this after synthesizing information from previous steps. The final answer should be clear, concise, and include reasoning and references to the 10K sections analyzed. Only call this function if you are confident the question has been answered completely or if the maximum step limit has been reached.",
                    "parameters" : {
                        "type" : "object",
                        "properties" : {
                            "final_answer": {
                                "type" : "string",
                                "description" : "The complete and final response to the original question. This should summarize key insights, include reasoning, and explicitly reference the relevant 10K sections (e.g., 'Based on ITEM_1A_RISK_FACTORS and ITEM_7A_MARKET_RISKS, the top three risks are...'). Ensure the response is concise and directly addresses the query."
                            }
                        }
                    }
                }
            }
        ]
        self.react_prompt = f"""
        You are a financial analyst specializing in company filings. Your goal is to analyze the 10-K form and answer questions precisely and efficiently.

        You have access to two tools:
        1. `get_10K_section`: Retrieve and filter text from a specific section of the latest 10-K document. Use this when specific insights from the filing are required.
        2. `get_10K_financial_statement`: Retrieve cash flow, income statement, or balance sheet from the 10K.
        2. `finish`: End the process once you have a complete answer, summarizing your reasoning and citing which 10-K sections informed your answer.

        *** PROCEDURE ***
        Follow this structured approach:
        - Thought: Reflect on the question and decide the next step. THIS IS A MANDATORY STEP AND CANNOT BE SKIPPED.
        - Action: Use one of the tools to gather information or conclude the process.
        - Observation: Record the result of the action and use it to inform the next step.
        - Repeat up to {MAX_STEPS} times or until the answer is complete.
        """.strip()
        self.messages = []
        self.dl = DataLayer(llm_client=data_analysis_client)

        self.company_tenk = get_latest_10K(self.company)
        if self.company_tenk is None:
            self.logger.error(f"No 10-K found for company: {self.company}")
            raise ValueError("No 10-K was found for this company")
        
        self.logger.info(f"Successfully initialized ReActAgent for company: {self.company}")

        self.tool_mappings = {
            "get_10K_section"  : self.analyze_10K_section_wrapper,
            "get_10K_financial_statement" : self.get_10K_financial_statement_wrapper,
            "finish" : self.finish
        }
    
    def analyze_10K_section_wrapper(self, section: str, rag_query: str = None) -> str:
        self.logger.info(f"Analyzing 10-K section: {section} with query: {rag_query}")
        try:
            result = self.dl.analyze_10K_section_helper(
                tenk=self.company_tenk, 
                section_name=section,
                rag_query=rag_query,
            )
            self.logger.debug(f"Successfully analyzed section {section}")
            self.logger.info(f"HERE IS THE SECTION RESULT:\n{result}")
            return result
        except Exception as e:
            self.logger.error(f"Error analyzing section {section}: {str(e)}")
            raise
    
    # TODO
    def _failsafe(self) -> str:
        # Naked API Call
        try:
                response = self.llm_client.chat.completions.create(
                    model="gpt-4o",
                    messages=self.messages,
                    tools=self.tools
                )
        except Exception as e:
            # Catastrophic failure
            raise
    
    def get_10K_financial_statement_wrapper(self, statement: str) -> str:
        self.logger.info(f"Retrieving {statement} from 10-K")
        try:
            result = self.dl.analyze_10K_finances_helper(
                tenk = self.company_tenk,
                section_name=statement
            )
            self.logger.debug(f"Successfully analyzed {statement}")
            self.logger.debug(f"Function Result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error analyzing section {statement}: {str(e)}")
            raise

    def invoke(self, query) -> int:
        self.logger.info(f"Starting analysis for query: {query}")
        self.react_prompt += f"""
        **** BEGIN PROCEDURE ****
        Question: {query}
        THOUGHT: """.strip()
        self.messages.append({"role": "system", "content":self.react_prompt})

        for i in range(MAX_STEPS * 2):
            self.logger.debug(f"Starting iteration {i+1}/{MAX_STEPS * 2}")
            
            try:
                self.logger.info(f"ON ITERATION {i}, sending {num_tokens_from_string(str(self.messages), "gpt-4o-mini")} tokens.")
                response = self.llm_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=self.messages,
                    tools=self.tools
                )
                
                response_message = response.choices[0].message.content
                response_tool_calls = response.choices[0].message.tool_calls
                
                if response_message is None and response_tool_calls is not None:
                    self.logger.info(f"ON ITERATION {i}, ONLY TOOL CALL WAS USED")
                    tool_call_content = f"Action: {response_tool_calls[0].function.name}({response_tool_calls[0].function.arguments})"
                    self.messages.append({
                        "role": "assistant",
                        "content": tool_call_content
                    })
                    self.logger.info(f"LLM action: {tool_call_content}")
                else:
                    self.logger.info(f"ON ITERATION {i}, THOUGHT WAS USED")
                    self.messages.append({"role": "assistant", "content": response_message})
                    self.logger.info(f"LLM thought: {response_message}")

                if response_tool_calls:
                    self.logger.info(f"ON ITERATION {i}, TOOL CALLS WAS USED")
                    tool_call = response_tool_calls[0]
                    fn = self.tool_mappings[tool_call.function.name]
                    self.logger.info(f"Executing function: {tool_call.function.name}")
                    self.logger.debug(f"Function arguments: {tool_call.function.arguments}")
                    
                    res = fn(**json.loads(tool_call.function.arguments))
                    
                    if tool_call.function.name == "finish":
                        self.logger.info("Analysis completed successfully")
                        return res
                        
                    self.messages.append({
                        "role": "system",
                        "content": f"Observation from `{tool_call.function.name}`: {res}"
                    })
                    
            except Exception as e:
                self.logger.error(f"Error during iteration {i+1}: {str(e)}")
                return self._failsafe()
                
        self.logger.warning(f"Maximum iterations ({MAX_STEPS * 2}) reached without completion")
        self.logger.warning(f"Entering failsafe procedure")
        self.logger.debug("Final message history: %s", self.messages)
        return self._failsafe()


    def finish(self, final_answer: str) -> str:
        # process chat history and encode as string
        self.logger.info("Finishing analysis")
        self.logger.debug(f"Final answer: {final_answer}")
        return final_answer

if __name__ == "__main__":
    ra = ReActAgent('AAPL', OpenAI(api_key=os.getenv('OPENAI_API_KEY')))
    ra.invoke("Identify and sum the total operating expenses. Are they growing faster than revenue?")
