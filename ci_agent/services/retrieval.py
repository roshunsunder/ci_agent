import os
from dotenv import load_dotenv
from openai import OpenAI
from ci_agent.services.tools import tools

load_dotenv("./.env")

class RetrievalLayer:
  def __init__(self, system_prompt):
    self.system_prompt = system_prompt
    self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

  def get_completion(self, user_content, model="gpt-4o-mini"):
      completion = self.client.chat.completions.create(
                  model=model,
                  messages=[
                      {"role": "system", "content": self.system_prompt},
                      {"role": "user", "content": user_content + f"\n\n##Tool Calls:"}
                  ],
                  tools=tools
              )
      print(f"Used: {completion.usage.total_tokens}")
      return completion.choices[0].message