"""
This is the class for the chatbot agent that the user will be able to ask questions to
"""
import os
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from react_agent import ReActAgent

load_dotenv()

class ChatResponse(BaseModel):
    response_text: str
    call_agent: bool
    agent_request_if_call_agent_true: str

class UIAgent:
    def __init__(self, company_ticker_or_cik):
        self.llm_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.agent = ReActAgent(company_ticker_or_cik, OpenAI(api_key=os.getenv('OPENAI_API_KEY')))
        self.system_prompt = f"""
        You are a helpful chatbot that helps users derive competitive intelligence on a particular company.
        Your job is to answer the user to the best of your ability. If you are unable to answer a question, it is okay to say so. If you need more clarification on the user's request, it is okay to ask.

        You have one tool at your disposal: an AI agent that has access to the company's 10-K, which is able to answer questions and do tasks. You should call this agent when the question the user is asking cannot (or should not) be answered without referencing the information found in the 10-K form. If the question can be answered without it, for example if the user is asking for clarification/elaboration, then do not call the agent.

        If you do decide to call this agent, you need to provide it a specific task, or ask it an answerable question.
        """.strip()

        self.chat_history = [{"role": "system", "content": self.system_prompt}]

        self.MAX_CHAT_TURNS = 30
    
    def _add_user_message(self, user_input: str):
        self.chat_history.append({"role":"user", "content":user_input})
    
    def _handle_chat_response(self, completion):
        chat_response : ChatResponse = completion.choices[0].message.parsed
        if chat_response.call_agent:
            self.agent.invoke(chat_response.agent_request_if_call_agent_true)
            

    
    def chat(self):
        for _ in range(self.MAX_CHAT_TURNS):
            user_input = input("Input: ")
            self._add_user_message(user_input)
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=self.chat_history
                response_format=ChatResponse,
            )
            self._handle_chat_response(completion)


event = completion.choices[0].message.parsed
print(event)
print(type(event))
print(event.response_text)