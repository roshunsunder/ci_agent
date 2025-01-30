import json
import os
import datetime
from typing import Generator, Optional, Union
from ci_agent.models.agent_models import AgentResponse
from dotenv import load_dotenv
from openai import OpenAI
from ci_agent.dependencies import public_companies_table
from ci_agent.services.retrieval import RetrievalLayer
from ci_agent.utils.mappings import FUNCTION_MAPPINGS

load_dotenv()

class Agent:
    def __init__(self, ent):
        self.ent = ent
        self.system_prompt = f"""
        You are an agent that produces competitive intelligence on {ent.display_name}.
        The current date is {datetime.date.today()}.

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
      item = public_companies_table.get_item(Key={'cik': str(self.ent.cik)}).get('Item', {})
      filings = item.get(filing_type, {})

      if not filings:
          return []  # Return an empty list if no filings are found

      # Handle date formatting and sorting
      if filing_type in ["10-K", "10-Q"]:
          # Dates are in "YYYY-MM-DD" format
          dates = sorted(filings.keys(), key=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"))
      elif filing_type == "8-K":
          # Dates are in "Month DD, YYYY" format
          dates = sorted(filings.keys(), key=lambda x: datetime.datetime.strptime(x, "%B %d, %Y"))

      return dates

    def readable_date_range(self, filing_type):
      available_dates = self.dates_available(filing_type)
      if not available_dates:
          return "NO AVAILABLE DATES"
      elif len(available_dates) == 1:
          return f"for the {available_dates[0]}"
      else:
          return f"from the dates {available_dates[0]} to {available_dates[-1]}"


    def chat(self, message: str, streaming: bool = False) -> Union[str, Generator[str, None, None]]:
        """Main chat function that handles both streaming and non-streaming responses."""
        self.messages.append({"role": "user", "content": message})
        
        # Get initial completion and handle information needs
        context = self._handle_information_needs()
        
        # If we have context, create a generator with it
        if context:
            messages_with_context = self._create_messages_with_context(context)
            response_generator = self.get_completion_stream(
                messages=messages_with_context, 
                model="gpt-4o-mini"
            )
        else:
            # No context needed, use original messages
            response_generator = self.get_completion_stream(
                messages=self.messages, 
                model="gpt-4o-mini"
            )

        if streaming:
            return self._stream_response(response_generator)
        else:
            return self._collect_response(response_generator)

    def _handle_information_needs(self) -> Optional[str]:
        """Handle information needs and return context if any."""
        response: AgentResponse = self.get_completion(self.messages, "gpt-4o", AgentResponse)
        
        if not response.information_needed:
            return None
            
        user_content = self._format_information_needs(response.information_needed)
        rl_message = self.rl.get_completion(user_content, "gpt-4o-mini")
        
        if not rl_message:
            return None
            
        return self._build_context(rl_message)

    def _format_information_needs(self, info_needed: list) -> str:
        """Format the information needs into a string."""
        content = "##Information Needed\n"
        for idx, step in enumerate(info_needed, 1):
            content += f"{idx}. {step}\n"
        return content

    def _build_context(self, rl_message) -> str:
        """Build context string from tool calls."""
        context = ""
        for tool_call in rl_message.tool_calls:
            context += f"# FROM : {tool_call.function.name}({tool_call.function.arguments})\n"
            context += f"{FUNCTION_MAPPINGS[tool_call.function.name](ent=self.ent, **json.loads(tool_call.function.arguments))}"
        return context

    def _create_messages_with_context(self, context: str) -> list:
        """Create messages list with context."""
        ephemeral_message = {
            "role": "system",
            "content": f"""The data retrieval mechanism for the assistant has \
            retrieved the following context which the assistant shall use to \
            answer the user's question. The assistant should be advised that the user cannot see this context:\n {context}""".strip()
        }
        
        messages = self.messages.copy()
        messages.append(ephemeral_message)
        
        # Add opaque context marker to original messages
        self.messages.append({
            "role": "system",
            "content": '<Context Made Opaque For This Step Due To Length>'
        })
        
        return messages

    def _stream_response(self, generator) -> Generator[str, None, None]:
        """Stream response chunks."""
        for chunk in generator:
            if chunk:
                yield chunk

    def _collect_response(self, generator) -> str:
        """Collect all response chunks into a single string."""
        return "".join(chunk for chunk in generator if chunk)

if __name__ == "__main__":
   a = Agent()