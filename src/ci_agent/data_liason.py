"""
Principle behind this class is to act as an intermediary between data accessor functions / RAG
and the driving agent. 
"""
import os
from dotenv import load_dotenv
from edgar_data_modules import (
    config_and_set_company,
    get_latest_10K,
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
)
from openai import OpenAI

DEFAULT_SYSTEM_PROMPT = """
You are an expert competitive analysis assistant. Your task is to analyze a information
(fincancial or otherwise) and extract key information that is relevant to the 
provided context and goal. Focus only on information that directly relates to 
the provided context and objective. Be concise but thorough in your analysis.
"""

class DataLiason:
    def __init__(self, llm_client, system_prompt: str = None):
        """ """
        self.llm_client = llm_client
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    def _analyze_10K_section_with_llm(
        self,
        section_content: str,
        context: str,
        overall_goal: str,
        section_description: str,
        max_tokens: int = 500,
    ):
        """
        Internal method for analyzing 10K sections
        """
        prompt = f"""
        Context: {context}
        Overall Goal: {overall_goal}
        Section: {section_description}
        
        Based on the context and goal above, analyze this {section_description} and
        extract only the most relevant information:

        **** SECTION CONTENT ****
        {section_content}
        **** END OF SECTION CONTENT ****
        
        Provide a concise analysis focusing only on information that directly relates
        to the context and goal. Ignore irrelevant details.
        """.strip()

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error calling LLM: {str(e)}")

    def analyze_10K_Item1_Business(
        self, context: str, goal: str, content, max_tokens: int = 500
    ) -> str:
        """
        Analyze Item 1 (Business Description) of the 10-K.

        Args:
            context: Current context or thought process of the agent
            goal: Overall objective or goal of the analysis
            max_tokens: Maximum tokens for LLM response
        """
        return self._analyze_10K_section_with_llm(
            content, context, goal, "Business Description (Item 1)", max_tokens
        )


if __name__ == "__main__":
    c = config_and_set_company('MSFT')
    tenk = get_latest_10K(c)
    load_dotenv()
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    dl = DataLiason(client)
    res = dl.analyze_10K_Item1_Business(
        content=get_10K_Item1_Business(tenk),
        goal="Identify key technological advantages",
        context="Evaluating competitive position"
    )
    print(res)

