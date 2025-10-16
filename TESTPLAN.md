# Test Plan - Finnhub API Migration

This document provides step-by-step instructions to test the Finnhub API integration after migration.

---

## Prerequisites

Before testing, ensure you have:

1. ✅ Python 3.10 or higher installed
2. ✅ `uv` package manager installed
3. ✅ Your `.env` file configured with:
   - `OPENAI_API_KEY=your-openai-api-key`
   - `FINNHUB_API_KEY=your-finnhub-api-key`

---

## Installation Steps

### 1. Install Dependencies

```bash
# From the project root directory
uv sync
```

This will:
- Install all Python dependencies from `pyproject.toml`
- Create a virtual environment
- Set up the `dexter-agent` command

**Expected Output:**
```
Resolved X packages in Y.YYs
Installed X packages in Y.YYs
```

### 2. Verify Environment Variables

```bash
# Check that your .env file has the correct keys
cat .env
```

**Expected Output:**
```
OPENAI_API_KEY=sk-...
FINNHUB_API_KEY=your-key-here
```

If your `.env` file doesn't exist:
```bash
cp env.example .env
# Then edit .env and add your actual API keys
```

---

## Quick Verification Test

Before running full tests, verify the tools can be imported:

```bash
# Test import
uv run python -c "from dexter.tools import get_income_statements, get_balance_sheets, get_cash_flow_statements; print('✅ Tools imported successfully')"
```

**Expected Output:**
```
✅ Tools imported successfully
```

---

## Test Cases

### Test 1: Basic Income Statement Query (Annual)

**Objective:** Verify that income statements can be fetched for annual periods

**Run:**
```bash
uv run dexter-agent
```

**Query:**
```
What was Apple's revenue for 2023?
```

**Expected Behavior:**
1. Agent creates tasks to fetch Apple's income statement
2. Tool calls `get_income_statements(ticker="AAPL", period="annual", limit=10)`
3. Data is fetched from Finnhub API
4. Agent extracts revenue information
5. Response includes specific revenue number for 2023

**Success Criteria:**
- ✅ No errors during API call
- ✅ Income statement data is returned
- ✅ Response includes Apple's 2023 revenue with specific dollar amount
- ✅ Data structure contains fields like "Revenue", "Revenues", or similar

**What to Look For:**
- Tool execution shows: "Executing get_income_statements..."
- Output contains numerical revenue data
- Final answer includes the actual revenue figure

---

### Test 2: Quarterly Balance Sheet Query

**Objective:** Verify that balance sheets can be fetched for quarterly periods

**Query:**
```
Show me Microsoft's total assets from their latest quarterly balance sheet
```

**Expected Behavior:**
1. Agent creates tasks to fetch Microsoft's balance sheet
2. Tool calls `get_balance_sheets(ticker="MSFT", period="quarterly", limit=1)`
3. Balance sheet data is fetched
4. Agent identifies total assets
5. Response includes specific assets figure

**Success Criteria:**
- ✅ Quarterly data is fetched (not annual)
- ✅ Balance sheet contains asset information
- ✅ Response shows most recent quarter's total assets
- ✅ Data includes fields like "Assets", "AssetsCurrent", or similar

---

### Test 3: Cash Flow Statement Query

**Objective:** Verify cash flow statements work correctly

**Query:**
```
What was Tesla's operating cash flow in the last 4 quarters?
```

**Expected Behavior:**
1. Agent creates tasks to fetch Tesla's cash flow statements
2. Tool calls `get_cash_flow_statements(ticker="TSLA", period="quarterly", limit=4)`
3. Cash flow data for 4 quarters is fetched
4. Agent extracts operating cash flow
5. Response shows data for all 4 quarters

**Success Criteria:**
- ✅ Data for 4 quarters is returned
- ✅ Operating cash flow information is present
- ✅ Response includes specific numbers for each quarter
- ✅ Fields include "NetCashProvidedByUsedInOperatingActivities" or similar

---

### Test 4: Multi-Company Comparison

**Objective:** Verify agent can handle queries involving multiple companies

**Query:**
```
Compare Amazon and Walmart's revenue for 2023
```

**Expected Behavior:**
1. Agent creates tasks to fetch income statements for both companies
2. Two separate tool calls:
   - `get_income_statements(ticker="AMZN", period="annual")`
   - `get_income_statements(ticker="WMT", period="annual")`
3. Both datasets are fetched
4. Agent compares revenue figures
5. Response includes both companies' revenues and comparison

**Success Criteria:**
- ✅ Both companies' data is fetched
- ✅ No errors or timeouts
- ✅ Response compares the two revenue figures
- ✅ Clear presentation of which company has higher revenue

---

### Test 5: Date Filtering

**Objective:** Verify date filtering with from_date parameter

**Query:**
```
Get Google's balance sheets from 2022 onwards
```

**Expected Behavior:**
1. Agent creates task to fetch balance sheets with date filter
2. Tool calls `get_balance_sheets(ticker="GOOGL", period="annual", from_date="2022-01-01")`
3. Only data from 2022 onwards is returned
4. Response includes 2022, 2023, and 2024 data (if available)

**Success Criteria:**
- ✅ from_date parameter is used correctly
- ✅ Returned data is filtered to 2022 and later
- ✅ No data from 2021 or earlier appears
- ✅ Multiple years of data are shown

---

### Test 6: Invalid Ticker Handling

**Objective:** Verify graceful error handling for invalid tickers

**Query:**
```
What is NOTAREALTICKER's revenue?
```

**Expected Behavior:**
1. Agent attempts to fetch data
2. API returns error or empty data
3. Agent handles the error gracefully
4. Response indicates the ticker was not found or data unavailable

**Success Criteria:**
- ✅ No application crash
- ✅ Graceful error message
- ✅ Agent doesn't retry infinitely
- ✅ User-friendly response

---

### Test 7: Out-of-Scope Query

**Objective:** Verify agent handles non-financial queries correctly

**Query:**
```
What is the weather like today?
```

**Expected Behavior:**
1. Planning agent returns empty task list (no financial tools needed)
2. No tool execution occurs
3. Answer agent responds using general knowledge
4. Response includes caveat about specializing in financial research

**Success Criteria:**
- ✅ No tool calls are made
- ✅ Agent responds appropriately
- ✅ Mentions it specializes in financial research
- ✅ No errors occur

---

## Manual API Test (Optional)

If you want to test the Finnhub API directly without running the agent:

```bash
# Create a test script
cat > test_finnhub.py << 'EOF'
import os
from dotenv import load_dotenv
from dexter.tools import get_income_statements

load_dotenv()

# Test basic API call
result = get_income_statements(ticker="AAPL", period="annual", limit=3)
print("✅ API call successful!")
print(f"Retrieved {len(result)} income statements")
if result:
    print(f"Latest data: Year {result[0]['year']}, Quarter {result[0]['quarter']}")
    print(f"Sample fields: {list(result[0]['data'].keys())[:5]}")
else:
    print("⚠️ No data returned")
EOF

# Run the test
uv run python test_finnhub.py
```

**Expected Output:**
```
✅ API call successful!
Retrieved 3 income statements
Latest data: Year 2024, Quarter 0
Sample fields: ['Revenue', 'CostOfRevenue', 'GrossProfit', ...]
```

---

## Troubleshooting

### Error: "FINNHUB_API_KEY not found"

**Solution:**
```bash
# Check your .env file exists
ls -la .env

# Verify it contains FINNHUB_API_KEY
cat .env | grep FINNHUB

# If missing, add it:
echo "FINNHUB_API_KEY=your-key-here" >> .env
```

### Error: HTTP 401 (Unauthorized)

**Cause:** Invalid API key

**Solution:**
1. Go to https://finnhub.io/dashboard
2. Copy your API key
3. Update `.env` file with correct key
4. Restart the agent

### Error: HTTP 429 (Rate Limit Exceeded)

**Cause:** Too many API calls (free tier: 60 calls/minute)

**Solution:**
- Wait 1 minute before retrying
- Reduce the number of queries
- Consider spacing out requests

### Error: "No data returned" for valid ticker

**Possible Causes:**
1. Company might not have SEC filings (non-US company)
2. Ticker symbol might be incorrect (use correct exchange symbol)
3. Date filter might be excluding all data

**Solution:**
- Verify ticker on https://finnhub.io/
- Try without date filters first
- Use common tickers (AAPL, MSFT, GOOGL) for initial testing

### Import Errors

**Solution:**
```bash
# Reinstall dependencies
uv sync --reinstall

# Or force clean install
rm -rf .venv
uv sync
```

---

## Performance Expectations

### API Response Times
- Single company, single period: ~1-3 seconds
- Multi-company query: ~3-6 seconds (multiple API calls)
- Complex analysis: ~10-20 seconds (planning + execution + validation)

### Rate Limits
- Free tier: 60 API calls/minute
- Approximately 1 call per second average
- Agent typically makes 1-3 API calls per query

---

## What Success Looks Like

After running all test cases, you should see:

✅ All 7 test cases pass
✅ No application crashes
✅ Accurate financial data in responses
✅ Graceful handling of errors
✅ Appropriate responses to out-of-scope queries
✅ Fast response times (under 20 seconds per query)

---

## Next Steps After Testing

If all tests pass:
1. Start using Dexter for real financial research
2. Monitor API usage at https://finnhub.io/dashboard
3. Consider upgrading to paid tier if you need:
   - Higher rate limits
   - TTM (Trailing Twelve Months) data
   - More historical data

If tests fail:
1. Check troubleshooting section above
2. Verify API keys are correct
3. Check internet connection
4. Review error messages carefully
5. Test direct API access using manual test script

---

## Exit the Agent

To exit Dexter at any time:
- Type `exit` or `quit`
- Or press `Ctrl+C`

---

## Support

If you encounter issues not covered in this test plan:
1. Check the Finnhub API documentation: https://finnhub.io/docs/api
2. Review the transition plan: [transitionplan.md](transitionplan.md)
3. Check your API key limits at: https://finnhub.io/dashboard
