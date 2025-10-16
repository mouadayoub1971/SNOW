# Transition Plan: Financial Datasets API → Finnhub API

## Overview
This document outlines a simple, step-by-step plan to migrate Dexter from the Financial Datasets API to the Finnhub API (free tier).

---

## Current State

### API Being Replaced
- **Provider**: Financial Datasets API (financialdatasets.ai)
- **Endpoints Used**:
  - `/financials/income-statements/`
  - `/financials/balance-sheets/`
  - `/financials/cash-flow-statements/`
- **Features**:
  - Supports: Annual, Quarterly, TTM periods
  - Date filtering: `report_period_gt`, `report_period_gte`, `report_period_lt`, `report_period_lte`
  - Standardized field names across companies

### Files Affected
1. [tools.py](src/dexter/tools.py) - All financial data tools
2. [env.example](env.example) - Environment variable template
3. [.env](.env) - User's actual environment file (not in git)
4. [README.md](README.md) - Documentation

---

## New State

### API Being Adopted
- **Provider**: Finnhub API (finnhub.io)
- **Primary Endpoint**: `/stock/financials-reported` (FREE tier)
- **Features**:
  - ✅ Supports: Annual, Quarterly
  - ❌ Does NOT support: TTM (Trailing Twelve Months)
  - ✅ All three statements in one response (income statement, balance sheet, cash flow)
  - Date filtering: `from`, `to` parameters (YYYY-MM-DD format)
  - As-reported data (field names may vary between companies)

### API Details
- **Base URL**: `https://finnhub.io/api/v1`
- **Authentication**: API key via query parameter `?token=YOUR_API_KEY`
- **Response Format**:
  ```json
  {
    "cik": "320193",
    "data": [
      {
        "symbol": "AAPL",
        "year": 2023,
        "quarter": 0,  // 0 = annual, 1-4 = quarterly
        "form": "10-K",
        "startDate": "2022-09-25",
        "endDate": "2023-09-30",
        "report": {
          "bs": { /* balance sheet */ },
          "ic": { /* income statement */ },
          "cf": { /* cash flow */ }
        }
      }
    ]
  }
  ```

---

## Migration Steps

### Step 1: Update Environment Variables
**Files to modify**: `env.example`, user's `.env` file

**Changes**:
```diff
# env.example
  # LLM API Keys
  OPENAI_API_KEY=your-openai-api-key

- # Stock Market API Key
- FINANCIAL_DATASETS_API_KEY=your-financial-datasets-api-key
+ # Financial Data API Key
+ FINNHUB_API_KEY=your-finnhub-api-key
```

**Action**:
- Update `env.example` file
- Users will need to get a free API key from https://finnhub.io/register
- Update their `.env` file accordingly

---

### Step 2: Refactor tools.py
**File**: [src/dexter/tools.py](src/dexter/tools.py)

#### 2.1 Update API Configuration
```python
# OLD
financial_datasets_api_key = os.getenv("FINANCIAL_DATASETS_API_KEY")
base_url = "https://api.financialdatasets.ai"

# NEW
finnhub_api_key = os.getenv("FINNHUB_API_KEY")
base_url = "https://finnhub.io/api/v1"
```

#### 2.2 Update Input Schema
Since Finnhub returns all three statements in one call, we can simplify:

```python
class FinancialStatementsInput(BaseModel):
    ticker: str = Field(description="The stock ticker symbol (e.g., 'AAPL')")
    period: Literal["annual", "quarterly"] = Field(
        description="The reporting period: 'annual' for yearly, 'quarterly' for quarterly"
    )
    limit: int = Field(
        default=10,
        description="The number of past financial statements to retrieve"
    )
    from_date: Optional[str] = Field(
        default=None,
        description="Filter: retrieve statements from this date onwards (YYYY-MM-DD)"
    )
    to_date: Optional[str] = Field(
        default=None,
        description="Filter: retrieve statements up to this date (YYYY-MM-DD)"
    )
```

**Key Changes**:
- Remove `report_period_gt/gte/lt/lte` (replaced with `from_date`, `to_date`)
- Remove `ttm` from period options (not supported on free tier)
- Simplified date filtering

#### 2.3 Update API Call Helper
```python
def call_finnhub_api(ticker: str, period: str, limit: int, from_date: Optional[str], to_date: Optional[str]) -> dict:
    """Helper function to call the Finnhub API."""
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
```

#### 2.4 Create Statement Extraction Functions
Since Finnhub returns all statements together, we need to extract specific ones:

```python
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
```

#### 2.5 Update Tool Functions
```python
@tool(args_schema=FinancialStatementsInput)
def get_income_statements(
    ticker: str,
    period: Literal["annual", "quarterly"],
    limit: int = 10,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> list:
    """Fetches a company's income statement, detailing its revenues, expenses, and net income.
    Useful for evaluating profitability and operational efficiency."""
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
    """Retrieves a company's balance sheet showing assets, liabilities, and shareholders' equity.
    Essential for assessing financial position."""
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
    """Provides a company's cash flow statement showing cash generation and usage.
    Key for understanding liquidity and solvency."""
    finnhub_data = call_finnhub_api(ticker, period, limit, from_date, to_date)
    return extract_cash_flow_statements(finnhub_data)
```

---

### Step 3: Update Documentation
**File**: [README.md](README.md)

**Changes needed**:
1. Update Prerequisites section:
   ```diff
   - Financial Datasets API key (get one at [financialdatasets.ai](https://financialdatasets.ai))
   + Finnhub API key (get one at [finnhub.io/register](https://finnhub.io/register))
   ```

2. Update installation step 3:
   ```diff
   # Edit .env and add your API keys
   # OPENAI_API_KEY=your-openai-api-key
   - # FINANCIAL_DATASETS_API_KEY=your-financial-datasets-api-key
   + # FINNHUB_API_KEY=your-finnhub-api-key
   ```

---

### Step 4: Update CLAUDE.md
**File**: [CLAUDE.md](CLAUDE.md)

**Changes needed**:
1. Update Environment Variables section:
   ```diff
   Required in `.env`:
   - `OPENAI_API_KEY`: OpenAI API key for LLM calls
   - - `FINANCIAL_DATASETS_API_KEY`: API key from financialdatasets.ai
   + - `FINNHUB_API_KEY`: API key from finnhub.io (free tier)
   ```

2. Add note about limitations:
   ```markdown
   ### API Limitations (Finnhub Free Tier)
   - ✅ Supports: Annual and Quarterly financial statements
   - ❌ Does NOT support: TTM (Trailing Twelve Months)
   - As-reported data: Field names may vary between companies
   - Rate limit: 60 API calls/minute on free tier
   ```

---

## Breaking Changes & Considerations

### 1. TTM Period No Longer Supported
**Impact**: Users who query "trailing twelve months" data will not get results

**Solution**: Update prompts to guide the agent:
- In [prompts.py](src/dexter/prompts.py), update `PLANNING_SYSTEM_PROMPT`:
  ```python
  PLANNING_SYSTEM_PROMPT = """...

  IMPORTANT: The financial data tools only support 'annual' and 'quarterly' periods.
  TTM (Trailing Twelve Months) is NOT available. If a user asks for TTM data,
  create tasks to fetch the most recent quarterly or annual data instead.
  ..."""
  ```

### 2. As-Reported Data (Non-Standardized)
**Impact**: Field names in responses may vary (e.g., "Revenue" vs "Revenues" vs "RevenueFromContractWithCustomer")

**Solution**: The LLM is flexible enough to handle varying field names. No code changes needed, but the Answer Agent should be aware:
- In [prompts.py](src/dexter/prompts.py), update `ANSWER_SYSTEM_PROMPT`:
  ```python
  ANSWER_SYSTEM_PROMPT = """...

  NOTE: Financial statement data comes directly from SEC filings (as-reported).
  Field names may vary between companies. Be flexible in identifying key metrics
  (e.g., revenue may appear as 'Revenue', 'Revenues', or 'RevenueFromContractWithCustomer').
  ..."""
  ```

### 3. Date Filtering Syntax Change
**Impact**: Agents need to use new date format

**Old format**: `report_period_gte="2023-01-01"`
**New format**: `from_date="2023-01-01"`

**Solution**: Update tool descriptions in [tools.py](src/dexter/tools.py) to clearly explain the new parameter names

### 4. Response Structure Change
**Impact**: The data structure returned is different

**Old structure**:
```json
{
  "income_statements": [
    { "revenue": 123, "net_income": 456, ... }
  ]
}
```

**New structure**:
```json
[
  {
    "symbol": "AAPL",
    "year": 2023,
    "quarter": 0,
    "data": { "Revenue": 123, "NetIncomeLoss": 456, ... }
  }
]
```

**Solution**: The extraction functions (Step 2.4) handle this transformation

---

## Testing Plan

### Manual Testing
After implementing changes, test with these queries:

1. **Annual data**: "What was Apple's revenue for 2023?"
2. **Quarterly data**: "Show me Microsoft's last 4 quarters of net income"
3. **Date filtering**: "Get Amazon's balance sheets from 2022 onwards"
4. **Multi-company**: "Compare Tesla and Ford's operating expenses for 2023"

### Expected Behavior
- Agent should successfully fetch data for annual/quarterly periods
- If user asks for TTM, agent should fetch quarterly data instead
- Date filtering should work with `from_date`/`to_date` parameters
- All three statement types should work correctly

---

## Rollback Plan

If the migration causes issues:

1. **Revert environment variables** in `env.example`:
   ```bash
   git checkout HEAD -- env.example
   ```

2. **Revert tools.py**:
   ```bash
   git checkout HEAD -- src/dexter/tools.py
   ```

3. **Revert documentation**:
   ```bash
   git checkout HEAD -- README.md CLAUDE.md
   ```

4. Users restore their `.env` file with old API key

---

## Timeline Estimate

| Step | Estimated Time |
|------|----------------|
| 1. Update env.example | 2 minutes |
| 2. Refactor tools.py | 30 minutes |
| 3. Update README.md | 5 minutes |
| 4. Update CLAUDE.md | 5 minutes |
| 5. Update prompts.py (optional) | 10 minutes |
| 6. Testing | 15 minutes |
| **Total** | **~1 hour** |

---

## Summary

This migration is **simple and straightforward** because:
1. ✅ Finnhub's free tier provides all three financial statements
2. ✅ We keep the same three tool functions (minimal API changes)
3. ✅ The response structure can be normalized with simple extraction functions
4. ✅ Only one endpoint needed: `/stock/financials-reported`

**Main trade-offs**:
- ❌ Lose TTM support (not critical for most use cases)
- ⚠️ As-reported data may have varying field names (LLM can handle this)
- ✅ Gain: Free tier, no cost concerns

**Next Steps**: Start with Step 1 (update environment variables) and proceed sequentially through the plan.
