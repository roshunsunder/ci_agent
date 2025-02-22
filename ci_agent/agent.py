import json
import os
import datetime
from boto3.dynamodb.conditions import Key, Attr
from typing import Generator, Optional, Union
from ci_agent.models.agent_models import AgentResponse
from dotenv import load_dotenv
from openai import OpenAI
from ci_agent.dependencies import public_companies_table
from ci_agent.services.retrieval import RetrievalLayer
from ci_agent.utils.mappings import FUNCTION_MAPPINGS, section_enums_mappings, tenq_section_enum_mappings

load_dotenv()

class Agent:
    def __init__(self, ent, start_date, data_sources):
        self.ent = ent
        self.start_date = start_date
        self.data_sources = data_sources
        self.system_prompt = f"""
        You are an agent that produces competitive intelligence on {ent.display_name}.
        The current date is {datetime.date.today()}.

        Your job is to answer the user to the best of your ability. \\
        If you are unable to answer a question, you must say so. \\
        If you need more clarification on the user's request, you must ask.

        You have the ability to do the following:
          - Retrieve entire 8-K document summaries by date range or latest entries.
            -- For 8-Ks, you have filing(s) available {self.readable_date_range("8-K")}.
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
    
    def generate_summary(self, filing, raw_text, doc_type, section_name=None):
        system_message = f"""Extract the key information from this {doc_type}. 
        Include financial information and key data if they exist. You will be penalized for generally describing and 
        summarizing as opposed to explicitly gathering particular information."""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": raw_text},
        ]

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Change model as needed
            messages=messages
        )

        return f"""# KEY INFO FROM {filing}{", " + section_name if section_name else ""} #\n""" + response.choices[0].message.content

    def dates_available(self, filing_type):
        """
        Retrieves an ordered list of available filing dates for the specified filing type (10-K, 10-Q, or 8-K)
        for the current company (based on self.ent.cik).

        Assumes that each filing is stored as a separate item in DynamoDB and that the table has a Global Secondary Index (GSI)
        with 'cik' as the partition key and 'filing_date' as the sort key (e.g., "cik-filing_date-index").

        Args:
            filing_type (str): The type of filing ('10-K', '10-Q', or '8-K').

        Returns:
            list: A list of ordered dates (as strings in "YYYY-MM-DD" format) for the specified filing type.
        """
        if filing_type not in ["10-K", "10-Q", "8-K"]:
            raise ValueError("Invalid filing type. Must be one of: '10-K', '10-Q', or '8-K'.")

        # Query the DynamoDB table using a GSI that indexes on 'cik' (and sorts by 'filing_date').
        response = public_companies_table.query(
            IndexName='cik-filing_date-index',  # Adjust the index name as configured in your table
            KeyConditionExpression=Key('cik').eq(str(self.ent.cik)),
            FilterExpression=Attr('filing_type').eq(filing_type)
        )

        items = response.get('Items', [])
        if not items:
            return []  # Return an empty list if no filings are found

        # Extract filing dates from the returned items.
        dates = [item['filing_date'] for item in items]

        # Sort the dates (assuming the dates are stored as "YYYY-MM-DD").
        dates.sort(key=lambda date_str: datetime.datetime.strptime(date_str, "%Y-%m-%d"))

        return dates


    def readable_date_range(self, filing_type):
      available_dates = self.dates_available(filing_type)
      if not available_dates:
          return "for NO AVAILABLE DATES"
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
        print(context)
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
    
    def handle_10_filing(self, ent, filing, generate_summary, filing_type, rewrite_summaries=False):
        """
        Stores or retrieves filing summaries (and financials) in a DynamoDB table where each item is
        keyed by a composite of cik, filing_type, and filing_date.

        Args:
            ent (object): An entity (e.g., a TenK or TenQ object) with company details.
            filing (object): The filing object containing raw text, filing date, and optionally financials.
            generate_summary (function): A function that accepts (filing, raw_text, filing_type, section_name)
                                        and returns a summary string.
            filing_type (str): Either "10-K" or "10-Q".
            rewrite_summaries (bool): If True, forces re-generation of the summaries even if they exist.

        Returns:
            dict: The DynamoDB item for the filing, including the summaries and financials.
        """
        # Choose the appropriate section mapping based on the filing_type.
        if filing_type == "10-K":
            section_mapping = section_enums_mappings  # Must be defined elsewhere
        elif filing_type == "10-Q":
            section_mapping = tenq_section_enum_mappings  # Must be defined elsewhere
        else:
            raise ValueError("filing_type must be either '10-K' or '10-Q'")

        table = public_companies_table  # Your DynamoDB table object
        filing_date = str(filing.filing_date)  # e.g., "2024-01-01"

        # Build a composite key (primary key) that uniquely identifies this filing.
        composite_key = f"{ent.cik}#{filing_type}#{filing_date}"

        # Step 1: Check if an item for this composite key already exists.
        response = table.get_item(Key={'cik_filing_date': composite_key})
        existing_item = response.get('Item')
        if existing_item and not rewrite_summaries:
            # The filing already exists and we are not rewriting summaries.
            return existing_item

        # Step 2: Generate summaries for each filing section.
        summaries = {}
        for section_name, section_enum in section_mapping.items():
            section_raw_text = filing[section_enum]
            if section_raw_text:
                summary = generate_summary(filing, section_raw_text, filing_type, section_name)
                summaries[section_enum] = {
                    'summary': summary
                }
            else:
                print(f"Section {section_name} not found in the filing.")

        # Step 3: Process financials if available.
        if hasattr(filing, 'financials') and filing.financials:
            financials = {
                "balance sheet": filing.financials.get_balance_sheet().data.drop(
                    ['style', 'concept', 'level'], axis=1
                ).to_markdown(),
                "income statement": filing.financials.get_income_statement().data.drop(
                    ['style', 'concept', 'level'], axis=1
                ).to_markdown(),
                "cash flow statement": filing.financials.get_cash_flow_statement().data.drop(
                    ['style', 'concept', 'level'], axis=1
                ).to_markdown()
            }
        else:
            financials = {}
        # Include financials under a dedicated key.
        summaries["financials"] = financials

        # Step 4: Create the new item with a composite primary key.
        new_item = {
            'cik_filing_date': composite_key,
            'cik': str(ent.cik),
            'filing_type': filing_type,
            'filing_date': filing_date,
            'summaries': summaries
        }

        # Step 5: Write the new item to the DynamoDB table.
        table.put_item(Item=new_item)

        # Return the newly created (or updated) filing item.
        return new_item


    
    def handle_eightk(self, ent, filing, generate_summary, rewrite_summaries=False):
        """
        Handles storing or retrieving the 8-K summary for a given filing date.

        Args:
            ent (object): An EightK object containing the filing information.
            generate_summary (function): A function that takes raw_text and returns a summary.

        Returns:
            str: The summary of the 8-K filing.
        """
        def get_eightk_filing_text(filing):
            eightk_repr = f"""##### {str(filing)} #####\n\n"""
            for item in filing.items:
                if item not in {'Item 9.01'}:
                    eightk_repr += f"**{str(item)}**\n"
                    eightk_repr += str(filing[item])
                    eightk_repr += "\n\n"
            return eightk_repr
        
        table = public_companies_table  # Replace with your table name
        filing_date = datetime.datetime.strptime(str(filing.date_of_report), "%B %d, %Y").strftime("%Y-%m-%d")
        raw_text = get_eightk_filing_text(filing)

        # Step 1: Try to fetch the item for the given cik
        # Build a composite key (primary key) that uniquely identifies this filing.
        composite_key = f"{ent.cik}#8-K#{filing_date}"

        # Step 1: Check if an item for this composite key already exists.
        response = table.get_item(Key={'cik_filing_date': composite_key})
        existing_item = response.get('Item')
        if existing_item and not rewrite_summaries:
            # The filing already exists and we are not rewriting summaries.
            return existing_item

        summary = generate_summary(filing, raw_text, "8-K")
        print(f"Extracting Key Info from {filing}")

        # Step 4: Write the new summary and raw_text to the database
        new_item = {
            'cik_filing_date': composite_key,
            'cik': str(ent.cik),
            'filing_type': "8-K",
            'filing_date': filing_date,
            'summary': summary
        }

        # Save the updated item back to the table
        table.put_item(Item=new_item)

        # Return the newly generated summary
        return summary
    def _handler_dispatcher(self, source_type, params):
        match source_type:
            case "10-K":
                self.handle_10_filing(
                    ent=params["ent"],
                    filing=params["filing"],
                    generate_summary=params["summary_generation_function"],
                    filing_type=params["source_type"],
                    rewrite_summaries=params["rewrite_summaries"]
                )
            case "10-Q":
                self.handle_10_filing(
                    ent=params["ent"],
                    filing=params["filing"],
                    generate_summary=params["summary_generation_function"],
                    filing_type=params["source_type"],
                    rewrite_summaries=params["rewrite_summaries"]
                )
            case "8-K":
                self.handle_eightk(
                    ent=params["ent"],
                    filing=params["filing"],
                    generate_summary=params["summary_generation_function"],
                    rewrite_summaries=params["rewrite_summaries"]
                )
            case _:
                raise ValueError("Unrecognized filing type")
                
    def init_data(self):
        for source in self.data_sources:
            dates = self.dates_available(source)
            print(f"Dates available for {source}: ", dates)
            filings = self.ent.get_filings(form=source).filter(date=f"{self.start_date}:{str(datetime.date.today())}")
            for filing in filings:
                f = filing.obj()
                if str(f.filing_date) not in dates:
                    print(f"Couldn't find {str(f.filing_date)} in database")
                    # Process
                    params = {
                        "ent" : self.ent,
                        "filing" : f,
                        "summary_generation_function" : self.generate_summary,
                        "source_type" : source,
                        "rewrite_summaries" : False
                    }
                    self._handler_dispatcher(source_type=source, params=params)
        print("LOADED SOURCES")


if __name__ == "__main__":
   a = Agent()