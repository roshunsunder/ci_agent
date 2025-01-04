"""Set of functions to interact with EDGAR data"""

import os
from typing import List
from edgar import Company, Financials, set_identity
from dotenv import load_dotenv

load_dotenv()

DATA_UNAVAILABLE_STR = "No data available"


def config_and_set_company(tickerOrCIK: str):
    """Will return a Company object after configuring"""
    set_identity(os.getenv("EDGAR_USER_AGENT"))
    return Company(tickerOrCIK)


def get_latest_10K(company):
    """Returns the 10K tenk object"""
    return company.latest("10-K").obj()


def get_10K_Item1_Business(tenk) -> str:
    res = tenk["Item 1"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item1A_Risk_Factors(tenk) -> str:
    res = tenk["Item 1A"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item1B_Unresolved_Staff_Comments(tenk) -> str:
    res = tenk["Item 1B"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item1C_Cybersecurity(tenk) -> str:
    res = tenk["Item 1C"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item2_Properties(tenk) -> str:
    res = tenk["Item 2"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item3_Legal_Proceedings(tenk) -> str:
    res = tenk["Item 3"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item4_Mine_Safety_Disclosures(tenk) -> str:
    res = tenk["Item 4"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item5_Market(tenk) -> str:
    res = tenk["Item 5"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item6_Consolidated_Financial_Data(tenk) -> str:
    res = tenk["Item 6"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item7_Managements_Discussion_and_Analysis(tenk) -> str:
    res = tenk["Item 7"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item7A_Market_Risks(tenk) -> str:
    res = tenk["Item 7A"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item8_Financial_Statements(tenk) -> str:
    res = tenk["Item 8"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item9_Changes_in_Accountants(tenk) -> str:
    res = tenk["Item 9"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item9A_Controls_and_Procedures(tenk) -> str:
    res = tenk["Item 9A"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item9B_Other_Information(tenk) -> str:
    res = tenk["Item 9B"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item10_Directors_Executive_Officers_and_Corporate_Governance(tenk) -> str:
    res = tenk["Item 10"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item11_Executive_Compensation(tenk) -> str:
    res = tenk["Item 11"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item12_Security_Ownership(tenk) -> str:
    res = tenk["Item 12"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item13_Related_Transactions_and_Director_Independence(tenk) -> str:
    res = tenk["Item 13"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item14_Principal_Accounting_Fees_and_Services(tenk) -> str:
    res = tenk["Item 14"]
    return DATA_UNAVAILABLE_STR if res is None else res


def get_10K_Item15_Exhibits_and_Financial_Statement_Schedules(tenk) -> str:
    res = tenk["Item 15"]
    return DATA_UNAVAILABLE_STR if res is None else res

def get_10K_balance_sheet(tenk) -> str:
    financials : Financials = tenk.financials
    bs = financials.get_balance_sheet()
    df = bs.get_dataframe()
    cleaned_df = df.drop('concept', axis=1, inplace=False)
    # TODO: test if str(cleaned_df) leads to better performance
    return cleaned_df.to_markdown()

def get_10K_income_statement(tenk) -> str:
    financials : Financials = tenk.financials
    bs = financials.get_income_statement()
    df = bs.get_dataframe()
    cleaned_df = df.drop('concept', axis=1, inplace=False)
    # TODO: test if str(cleaned_df) leads to better performance
    return cleaned_df.to_markdown()

def get_10K_cash_flow(tenk) -> str:
    financials : Financials = tenk.financials
    bs = financials.get_cash_flow_statement()
    df = bs.get_dataframe()
    cleaned_df = df.drop('concept', axis=1, inplace=False)
    # TODO: test if str(cleaned_df) leads to better performance
    return cleaned_df.to_markdown()

if __name__ == "__main__":
    c = config_and_set_company('AAPL')
    tenk = get_latest_10K(c)
    print(get_10K_cash_flow(tenk))
