"""Agent that handles the ReACT CoT"""
import os
import json
from openai import OpenAI
from data_liason import DataLiason
from edgar_data_modules import (
    config_and_set_company,
    get_latest_10K
)
from dotenv import load_dotenv

load_dotenv()


MAX_STEPS = 5

class ReActAgent:
    def __init__(self, company_ticker_or_cik, data_analysis_client):
        self.llm_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.company = config_and_set_company(company_ticker_or_cik)
        if self.company is None:
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
                                "enum" : ['ITEM_01_BUSINESS', 'ITEM_1A_RISK_FACTORS', 'ITEM_1B_UNRESOLVED_STAFF_COMMENTS', 'ITEM_1C_CYBERSECURITY', 'ITEM_02_PROPERTIES', 'ITEM_03_LEGAL_PROCEEDINGS', 'ITEM_04_MINE_SAFETY_DISCLOSURES', 'ITEM_05_MARKET', 'ITEM_06_CONSOLIDATED_FINANCIAL_DATA', 'ITEM_07_MGMT_DISCUSSION_AND_ANALYSIS', 'ITEM_7A_MARKET_RISKS', 'ITEM_08_FINANCIAL_STATEMENTS', 'ITEM_09_CHANGES_IN_ACCOUNTANTS', 'ITEM_9A_CONTROLS_AND_PROCEDURES', 'ITEM_9B_OTHER_INFORMATION', 'ITEM_10_DIRECTORS_EXECUTIVE_OFFICERS_AND_GOVERNANCE', 'ITEM_11_EXECUTIVE_COMPENSATION', 'ITEM_12_SECURITY_OWNERSHIP', 'ITEM_13_RELATED_TRANSACTIONS_AND_DIRECTOR_INDEPENDENCE', 'ITEM_14_PRINCIPAL_ACCOUNTING_FEES_AND_SERVICES', 'ITEM_15_EXHIBITS_AND_FINANCIAL_STATEMENT_SCHEDULES'],
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
        2. `finish`: End the process once you have a complete answer, summarizing your reasoning and citing which 10-K sections informed your answer.

        *** PROCEDURE ***
        Follow this structured approach:
        - Thought: Reflect on the question and decide the next step.
        - Action: Use one of the tools to gather information or conclude the process.
        - Observation: Record the result of the action and use it to inform the next step.
        - Repeat up to {MAX_STEPS} times or until the answer is complete.
        """.strip()
        self.messages = []
        self.dl = DataLiason(llm_client=data_analysis_client)

        self.company_tenk = get_latest_10K(self.company)
        if self.company_tenk is None:
            raise ValueError("No 10-K was found for this company")

        self.tool_mappings = {
            "get_10K_section"  : self.analyze_10K_section_wrapper,
            "finish" : self.finish
        }
    
    def analyze_10K_section_wrapper(self, section: str, rag_query: str = None) -> str:
        return self.dl.analyze_10K_section_helper(
            tenk=self.company_tenk, 
            section_name=section,
            rag_query=rag_query,
        )

    def invoke(self, query):
        self.react_prompt += f"""
        **** BEGIN PROCEDURE ****
        Question: {query}
        THOUGHT: """.strip()
        self.messages.append({"role": "system", "content":self.react_prompt})

        for i in range(MAX_STEPS * 2):
            response = self.llm_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=self.messages,
                tools=self.tools
            )
            # check if empty content
            response_message = response.choices[0].message.content
            response_tool_calls = response.choices[0].message.tool_calls
            if response_message is None and response_tool_calls is not None:
                self.messages.append({
                    "role":"assistant", 
                    "content":f"Action: {response_tool_calls[0].function.name}({response_tool_calls[0].function.arguments})"
                })
            else:
                self.messages.append({"role":"assistant", "content":response_message})
            print(">>>>>>>>>> LLM IDEA: ", response.choices[0].message.content)
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                fn = self.tool_mappings[tool_call.function.name]
                print(">>>>>>>>>> FUNCTION CALL: ", tool_call.function.name)
                res = fn(**json.loads(tool_call.function.arguments))
                print(">>>>>>>>>> FUNCTION ARGS: ", tool_call.function.arguments)
                if tool_call.function.name == "final":
                    return
                self.messages.append({"role":"system", "content":f"Observation from `{tool_call.function.name}`: {res}"})
        print("MAX ITERATIONS REACHED")
        print(self.messages)


    def finish(self, final_answer: str) -> str:
        # process chat history and encode as string
        print("FINAL CALLED")
        print(final_answer)
        exit(0)

if __name__ == "__main__":
    ra = ReActAgent('AAPL', OpenAI(api_key=os.getenv('OPENAI_API_KEY')))
    ra.invoke("What initiatives are highlighted under Corporate Social Responsibility (CSR), and how do they align with the company’s business goals?")