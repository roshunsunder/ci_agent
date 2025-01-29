from models import AgentResponse
from openai import OpenAI
from datetime import date

class Agent:
    def __init__(self, ent):
        self.system_prompt = f"""
        You are an agent that produces competitive intelligence on {ent.display_name}.
        The current date is {date.today()}.

        Your job is to answer the user to the best of your ability. \\
        If you are unable to answer a question, you must say so. \\
        If you need more clarification on the user's request, you must ask.

        You have the ability to do the following:
          - Retrieve entire 8-K document summaries by date range or latest entries.
          - Retrieve specific financial statements from 10-K filings (balance sheet, income statement, cash flow statement)."
          - Retrieve specific item summaries of 10-K documents by date range or latest entries (these are standard items like 1. Business, 1A. Risk, , etc.).
            -- Note: for financial information, do not retrieve Item 8. That is what the previous function is for.
            -- For 10-Ks, you have filing(s) available {self.readable_date_range("10-K")}.
          - Retrieve specific financial statements from 10-Q filings (balance sheet, income statement, cash flow statement)."
          - Retrieve specific item summaries of 10-Q documents by date range or latest entries (these are standard items like 1. Business, 1A. Risk, , etc.).
            -- Note: for financial information, do not retrieve Item 1. That is what the previous function is for.
            -- For 10-Qs, you have filing(s) available {self.readable_date_range("10-Q")}.

        If a user query pertains to more than one of these items, put multiple entries in the information_needed field, as you will synethesize the data together.

        After receiving context from the data retrieval mechanism, you will be penalized for not citing your sources in the format: 'Source: <source name>, <section name (if available)>, <date (if available)>'.
        """.strip()

        self.retrieval_layer_system_prompt = """You are a data assistant. You are to take in an ordered list of pieces of information to retrieve. \\
        You are to return a list of tool calls that correspond to each of the pieces of information requested.""".strip()

        self.messages = [
          {"role": "system", "content": self.system_prompt}
        ]

        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.rl = RetrievalLayer(self.retrieval_layer_system_prompt)
        self.MAX_CHAT_TURNS = 30

    def get_completion(self, messages, model="gpt-4o-mini", format=None):
      completion = self.client.beta.chat.completions.parse(
          model=model,
          messages=messages,
          response_format=format,
      )
      response = completion.choices[0].message.parsed
      print(f"used: {completion.usage.total_tokens}")
      print("*" * 100)
      return response

    def get_completion_stream(self, messages, model="gpt-4o-mini"):
      response = self.client.chat.completions.create(
          model=model,
          messages=messages,
          temperature=0,
          stream=True  # this time, we set stream=True
      )

      for chunk in response:
          yield chunk.choices[0].delta.content

    def dates_available(self, filing_type):
      """
      Retrieves an ordered list of available dates for the specified filing type (10-K, 10-Q, or 8-K).

      Args:
          filing_type (str): The type of filing ('10-K', '10-Q', or '8-K').

      Returns:
          list: A list of ordered dates for the specified filing type.
      """
      if filing_type not in ["10-K", "10-Q", "8-K"]:
          raise ValueError("Invalid filing type. Must be one of: '10-K', '10-Q', or '8-K'.")

      # Query the database for the company's filings
      item = table.get_item(Key={'cik': str(ent.cik)}).get('Item', {})
      filings = item.get(filing_type, {})

      if not filings:
          return []  # Return an empty list if no filings are found

      # Handle date formatting and sorting
      if filing_type in ["10-K", "10-Q"]:
          # Dates are in "YYYY-MM-DD" format
          dates = sorted(filings.keys(), key=lambda x: datetime.strptime(x, "%Y-%m-%d"))
      elif filing_type == "8-K":
          # Dates are in "Month DD, YYYY" format
          dates = sorted(filings.keys(), key=lambda x: datetime.strptime(x, "%B %d, %Y"))

      return dates

    def readable_date_range(self, filing_type):
      available_dates = self.dates_available(filing_type)
      if not available_dates:
          return "NO AVAILABLE DATES"
      elif len(available_dates) == 1:
          return f"for the {available_dates[0]}"
      else:
          return f"from the dates {available_dates[0]} to {available_dates[-1]}"


    def chat(self):
      for _ in range(self.MAX_CHAT_TURNS):
        message = input("User: ")
        self.messages.append({"role" : "user" , "content" : message})
        response : AgentResponse = self.get_completion(self.messages, "gpt-4o", AgentResponse)
        user_content = "##Information Needed\n"
        rl_message = None
        if response.information_needed:
          print(response.information_needed)
          for idx, step in enumerate(response.information_needed):
            user_content += f"{idx+1}. {step}\n"
          rl_message = self.rl.get_completion(user_content, "gpt-4o-mini")
          print(rl_message)

        # Construct context
        generator = None
        if rl_message:
          context = ""
          for tool_call in rl_message.tool_calls:
            context += f"# FROM : {tool_call.function.name}({tool_call.function.arguments})\n"
            context += f"{FUNCTION_MAPPINGS[tool_call.function.name](**json.loads(tool_call.function.arguments))}"
          eph = [{
              "role" : "system",
              "content" : f"""The data retrieval mechanism for the assistant has \\
              retrieved the following context which the assistant shall use to \\
              answer the user's question. The assistant should be advised that the user cannot see this context:\n {context}""".strip()
          }]
        generator = self.get_completion_stream(messages=self.messages + eph, model="gpt-4o-mini")
        if rl_message:
          self.messages.append({
              "role" : "system",
              "content" : f'<Context Made Opaque For This Step Due To Length>'
          })

        # Iterating over the generator and printing each chunk as it's received
        for chunk in generator:
            if chunk:  # Check if chunk has content
                print(chunk, end='', flush=True)

if __name__ == "__main__":
   a = Agent()