# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dexter is an autonomous financial research agent that performs deep analysis using task planning, self-reflection, and real-time market data. It's built specifically for financial research and uses a multi-agent architecture with specialized components.

## Essential Commands

### Setup
```bash
# Install dependencies
uv sync

# Setup environment variables (required)
cp env.example .env
# Edit .env and add:
# - OPENAI_API_KEY
# - FINNHUB_API_KEY (from finnhub.io - free tier)
```

### Running the Agent
```bash
# Run Dexter in interactive mode
uv run dexter-agent
```

## Architecture

### Multi-Agent System
Dexter uses a coordinated agent architecture with four specialized components that work together:

1. **Planning Agent** ([agent.py:26-43](src/dexter/agent.py#L26-L43))
   - Analyzes user queries and decomposes them into structured task lists
   - Returns empty task list if query is out of scope (non-financial)
   - Uses `PLANNING_SYSTEM_PROMPT` and outputs `TaskList` schema

2. **Action Agent** ([agent.py:46-59](src/dexter/agent.py#L46-L59))
   - Selects appropriate tools to execute research steps
   - Receives task description and history of tool outputs
   - Returns `AIMessage` with tool calls or no tool calls if task cannot be done with available tools
   - Uses `ACTION_SYSTEM_PROMPT`

3. **Validation Agent** ([agent.py:62-74](src/dexter/agent.py#L62-L74))
   - Checks if tasks are complete based on collected data
   - Returns boolean indicating task completion
   - Uses `VALIDATION_SYSTEM_PROMPT` and outputs `IsDone` schema

4. **Answer Agent** ([agent.py:176-189](src/dexter/agent.py#L176-L189))
   - Synthesizes all collected data into comprehensive responses
   - Uses `ANSWER_SYSTEM_PROMPT` and outputs `Answer` schema
   - Handles both in-scope (financial) and out-of-scope queries

### Main Execution Loop
The agent's `run()` method ([agent.py:92-172](src/dexter/agent.py#L92-L172)) orchestrates the entire process:

1. Plans tasks using Planning Agent
2. Iterates through tasks until all are completed
3. For each task:
   - Asks Action Agent what to do (with full session history)
   - Executes tool calls
   - Accumulates outputs in `session_outputs` list (used across entire session)
   - Validates task completion
4. Generates final answer using all accumulated data

**Important patterns:**
- `session_outputs` accumulates ALL tool outputs for the entire session and is passed to both Action and Validation agents
- `last_actions` tracks the last 4 actions to detect infinite loops
- Two safety limits: `max_steps` (global) and `max_steps_per_task` (per-task iterations)

### Tools System
Financial data tools are defined in [tools.py](src/dexter/tools.py) using LangChain's `@tool` decorator:

- `get_income_statements()`: Revenue, expenses, net income
- `get_balance_sheets()`: Assets, liabilities, shareholders' equity
- `get_cash_flow_statements()`: Cash generation and usage

All tools:
- Use `FinancialStatementsInput` Pydantic schema for validation
- Support `annual` and `quarterly` periods (TTM not supported)
- Support filtering by date ranges (from_date/to_date in YYYY-MM-DD format)
- Call the Finnhub API via `call_finnhub_api()` helper
- Extract specific statement types from combined Finnhub response
- Are registered in the `TOOLS` list (exported to agent)

### LLM Interface
[model.py](src/dexter/model.py) provides a unified `call_llm()` function that handles:
- Structured output via Pydantic schemas (`with_structured_output`)
- Tool binding for function calling (`bind_tools`)
- System prompt injection
- Uses GPT-4o by default

### State Management
The agent maintains three key state variables during execution:
- `step_count`: Global step counter for safety limits
- `session_outputs`: List of all tool outputs (persists across all tasks)
- `last_actions`: Recent action signatures for loop detection

## Key Concepts

### Safety Features
- **Loop Detection**: Tracks last 4 actions; aborts if same action repeats 4 times ([agent.py:141-146](src/dexter/agent.py#L141-L146))
- **Step Limits**: Global `max_steps` (default 20) and per-task `max_steps_per_task` (default 5)
- **Graceful Degradation**: If no tool calls returned, marks task as done to avoid infinite loops

### Data Flow
1. User query → Planning Agent → Task list
2. For each task:
   - Task + session history → Action Agent → Tool calls
   - Tool execution → Results added to session_outputs
   - Task + session history → Validation Agent → Done/not done
3. Query + all session_outputs → Answer Agent → Final response

### Out-of-Scope Handling
When queries are not financial research related:
- Planning Agent returns empty task list
- System skips task execution loop
- Answer Agent generates response using general knowledge

## Environment Variables

Required in `.env`:
- `OPENAI_API_KEY`: OpenAI API key for LLM calls
- `FINNHUB_API_KEY`: API key from finnhub.io (free tier)

### API Limitations (Finnhub Free Tier)
- ✅ Supports: Annual and Quarterly financial statements
- ❌ Does NOT support: TTM (Trailing Twelve Months)
- As-reported data: Field names may vary between companies (from SEC filings)
- Rate limit: 60 API calls/minute on free tier
- Endpoint used: `/stock/financials-reported` - returns all three statements (bs, ic, cf) in one call

## Python Requirements

- Python 3.10+
- Package manager: `uv` (not pip)
- Dependencies managed in [pyproject.toml](pyproject.toml)
- Entry point: `dexter-agent` command maps to `dexter.cli:main`
