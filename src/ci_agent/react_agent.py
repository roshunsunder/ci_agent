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
                    "name": "analyze_10K_section",
                    "description": "Call this function if you want to access the company's 10K. Denoting a section will simply return the parsed text of the 10K document, which you can filter by using a search query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "section": {
                                "type": "string",
                                "enum" : ['ITEM_01_BUSINESS', 'ITEM_1A_RISK_FACTORS', 'ITEM_1B_UNRESOLVED_STAFF_COMMENTS', 'ITEM_1C_CYBERSECURITY', 'ITEM_02_PROPERTIES', 'ITEM_03_LEGAL_PROCEEDINGS', 'ITEM_04_MINE_SAFETY_DISCLOSURES', 'ITEM_05_MARKET', 'ITEM_06_CONSOLIDATED_FINANCIAL_DATA', 'ITEM_07_MGMT_DISCUSSION_AND_ANALYSIS', 'ITEM_7A_MARKET_RISKS', 'ITEM_08_FINANCIAL_STATEMENTS', 'ITEM_09_CHANGES_IN_ACCOUNTANTS', 'ITEM_9A_CONTROLS_AND_PROCEDURES', 'ITEM_9B_OTHER_INFORMATION', 'ITEM_10_DIRECTORS_EXECUTIVE_OFFICERS_AND_GOVERNANCE', 'ITEM_11_EXECUTIVE_COMPENSATION', 'ITEM_12_SECURITY_OWNERSHIP', 'ITEM_13_RELATED_TRANSACTIONS_AND_DIRECTOR_INDEPENDENCE', 'ITEM_14_PRINCIPAL_ACCOUNTING_FEES_AND_SERVICES', 'ITEM_15_EXHIBITS_AND_FINANCIAL_STATEMENT_SCHEDULES'],
                                "description" : "This is an enum value to choose which section of the 10K you'd like to access."
                                },
                            "rag_query" : {
                                "type": "string",
                                "description" : "This is a search query that, using vector similarity, filters which paragraphs you receive from the raw text of the 10K Item that you denoted with the `section` parameter."
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
                    "description" : "This function is only to be called when you have gotten the final answer for the question asked to you or if it has taken more than 3 steps to answer the question. This will end the chain of thought.",
                    "parameters" : {
                        "type" : "object",
                        "properties" : {
                            "final_answer": {
                                "type" : "string",
                                "description" : "This should be the final answer to the overall question. Here, you must use the history of the chat to succintly provide the answer, including a description of which sources were used to inform said answer."
                            }
                        }
                    }
                }
            }
        ]
        self.react_prompt = f"""
        You are an expert in company analysis, be it financial, strategic or otherwise. Your job is to follow a procedure to answer the question or task that is given to you regarding a particular company, to the best of your ability.

        To assist with this procedure, you have the following tools:
        {self.tools}

        **** PROCEDURE DESCRIPTION ****
        The procedure follows the following format.

        - Thought: think about what to do next
        - Action: the action to take, should be one of the aforementioned tools.
        - Observation: The result of the action.
        ... (this Thought/Action/Observation can repeat up to {MAX_STEPS} times. You should try, however, to reach the final answer in as few steps as possible.)
        - Thought: I now know the final answer
        - Final Answer: the final answer to the original input question

        Always work one step at a time (step being Thought, Action, or Observation). The idea is that we break the problem down into steps. Sometimes, \\
        a question may be simple enough that it can be answered in one cycle.

        **** END OF PROCEDURE DESCRIPTION ****

        """.strip()
        self.messages = []
        self.dl = DataLiason(llm_client=data_analysis_client)

        self.company_tenk = get_latest_10K(self.company)
        if self.company_tenk is None:
            raise ValueError("No 10-K was found for this company")

        self.tool_mappings = {
            "analyze_10K_section"  : self.analyze_10K_section_wrapper,
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
                self.messages.append({"role":"system", "content":f"OBSERVATION: {res}"})
        print("MAX ITERATIONS REACHED")
        print(self.messages)


    def finish(self, final_answer: str) -> str:
        # process chat history and encode as string
        print("FINAL CALLED")
        print(final_answer)
        exit(0)

if __name__ == "__main__":
    ra = ReActAgent('MSFT', OpenAI(api_key=os.getenv('OPENAI_API_KEY')))
    ra.invoke("Based on the risk factors section, what are the top three risks that could impact the company’s financial performance?")