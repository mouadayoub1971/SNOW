from langchain.tools import tool
from typing import List, Callable, Literal, Optional
import requests
import os
from pydantic import BaseModel, Field

####################################
# Tools
####################################
finnhub_api_key = os.getenv("FINNHUB_API_KEY")

class FinancialStatementsInput(BaseModel):
    ticker: str = Field(description="The stock ticker symbol to fetch financial statements for. For example, 'AAPL' for Apple.")
    period: Literal["annual", "quarterly"] = Field(description="The reporting period for the financial statements. 'annual' for yearly, 'quarterly' for quarterly.")
    limit: int = Field(default=10, description="The number of past financial statements to retrieve.")
    from_date: Optional[str] = Field(default=None, description="Optional filter to retrieve financial statements from this date onwards (format: YYYY-MM-DD).")
    to_date: Optional[str] = Field(default=None, description="Optional filter to retrieve financial statements up to this date (format: YYYY-MM-DD).")


def call_finnhub_api(ticker: str, period: str, limit: int, from_date: Optional[str], to_date: Optional[str]) -> dict:
    """Helper function to call the Finnhub API."""
    base_url = "https://finnhub.io/api/v1"
    url = f"{base_url}/stock/financials-reported"

    params = {
        "symbol": ticker,
        "freq": period,  # 'annual' or 'quarterly'
        "token": finnhub_api_key
    }

    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Limit results if needed (Finnhub doesn't have limit param)
    if "data" in data and len(data["data"]) > limit:
        data["data"] = data["data"][:limit]

    return data


def extract_income_statements(finnhub_data: dict) -> list:
    """Extract income statements from Finnhub response."""
    results = []
    for report in finnhub_data.get("data", []):
        ic_data = report.get("report", {}).get("ic", {})
        if ic_data:
            results.append({
                "symbol": report.get("symbol"),
                "year": report.get("year"),
                "quarter": report.get("quarter"),
                "start_date": report.get("startDate"),
                "end_date": report.get("endDate"),
                "form": report.get("form"),
                "data": ic_data
            })
    return results


def extract_balance_sheets(finnhub_data: dict) -> list:
    """Extract balance sheets from Finnhub response."""
    results = []
    for report in finnhub_data.get("data", []):
        bs_data = report.get("report", {}).get("bs", {})
        if bs_data:
            results.append({
                "symbol": report.get("symbol"),
                "year": report.get("year"),
                "quarter": report.get("quarter"),
                "start_date": report.get("startDate"),
                "end_date": report.get("endDate"),
                "form": report.get("form"),
                "data": bs_data
            })
    return results


def extract_cash_flow_statements(finnhub_data: dict) -> list:
    """Extract cash flow statements from Finnhub response."""
    results = []
    for report in finnhub_data.get("data", []):
        cf_data = report.get("report", {}).get("cf", {})
        if cf_data:
            results.append({
                "symbol": report.get("symbol"),
                "year": report.get("year"),
                "quarter": report.get("quarter"),
                "start_date": report.get("startDate"),
                "end_date": report.get("endDate"),
                "form": report.get("form"),
                "data": cf_data
            })
    return results


@tool(args_schema=FinancialStatementsInput)
def get_income_statements(
    ticker: str,
    period: Literal["annual", "quarterly"],
    limit: int = 10,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> list:
    """Fetches a company's income statement, detailing its revenues, expenses, and net income over a reporting period. Useful for evaluating a company's profitability and operational efficiency."""
    finnhub_data = call_finnhub_api(ticker, period, limit, from_date, to_date)
    return extract_income_statements(finnhub_data)


@tool(args_schema=FinancialStatementsInput)
def get_balance_sheets(
    ticker: str,
    period: Literal["annual", "quarterly"],
    limit: int = 10,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> list:
    """Retrieves a company's balance sheet, which provides a snapshot of its assets, liabilities, and shareholders' equity at a specific point in time. Essential for assessing a company's financial position."""
    finnhub_data = call_finnhub_api(ticker, period, limit, from_date, to_date)
    return extract_balance_sheets(finnhub_data)


@tool(args_schema=FinancialStatementsInput)
def get_cash_flow_statements(
    ticker: str,
    period: Literal["annual", "quarterly"],
    limit: int = 10,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> list:
    """Provides a company's cash flow statement, showing how cash is generated and used across operating, investing, and financing activities. Key for understanding a company's liquidity and solvency."""
    finnhub_data = call_finnhub_api(ticker, period, limit, from_date, to_date)
    return extract_cash_flow_statements(finnhub_data)


TOOLS: List[Callable[..., any]] = [
    get_income_statements,
    get_balance_sheets,
    get_cash_flow_statements,
]

RISKY_TOOLS = {}  # guardrail: require confirmation
