# Dune + Gemini On-Chain Data Analysis Assistant

Leverage Gemini's function calling to drive the Dune API, creating a complete closed loop from "natural language questions → on-chain data → AI analysis."

## Architecture Flow

```
① User question (e.g., "What has this wallet done in the last 7 days?")
        │
        ▼
② Gemini API understands intent and decides which tool to call (function calling)
        │
        ▼
③ Python executes the corresponding function and calls the Dune API
        │
        ▼
④ Dune returns on-chain data (balances / transactions / transfers / custom SQL results)
        │
        ▼
⑤ Python packages the data as function_response and returns it to Gemini
        │
        ▼
⑥ Gemini generates natural language analysis combining the data
        │
        ▼
"This wallet has conducted xx transactions in the last 7 days, primarily interacting with xxx contracts..."
```

## File Structure

```
dune_gemini_agent/
├── config.py          # Read API keys and configuration
├── dune_client.py      # Dune API low-level wrapper (SQL queries + on-chain data interfaces)
├── tools.py            # Gemini tool (function calling) schema + dispatch table
├── gemini_agent.py      # Core orchestration: intent recognition → tool invocation → analysis summary
├── main.py             # Command-line entry point
├── requirements.txt
└── .env.example
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
```
GEMINI_API_KEY=Your Gemini API Key      # https://aistudio.google.com/apikey
DUNE_API_KEY=Your Dune API Key          # https://dune.com/settings/api
GEMINI_MODEL=gemini-2.0-flash           # Can be changed to other function-calling supported models
```
### 3. Run
```bash
python main.py
```
Example interaction：
```
You: Help me check the recent token transfers for wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

## Two Ways to "Generate SQL / Query Intent"

Gemini currently provides **4 tools**，corresponding to two usage approaches：

1. **Directly call Dune's on-chain data interfaces**（no need to write SQL, fast response）
   - `get_wallet_balances`：Current token balance snapshot
   - `get_wallet_transactions`：Recent native transaction history
   - `get_token_transfers`：Recent token incoming/outgoing records

2. **Execute custom SQL queries**（`run_dune_sql_query`）
   - Suitable for complex aggregate statistics, e.g., "Which contracts has this wallet interacted with most in the last 7 days?" "Net inflow of a specific token over the last 30 days," etc.
   - **Prerequisite**：You must first write and save a query in SQL on the [Dune web interface](https://dune.com/) ,and obtain the `query_id`.You can use placeholders like  `{{wallet_address}}` and `{{days}}` in the SQL to create parameterized queries ,which Gemini will pass via `params` when calling.
   - Example SQL (Dune SQL / Trino syntax, for reference only):
     ```sql
     select
         to_address,
         count(*) as tx_count,
         sum(value / 1e18) as total_eth
     from ethereum.transactions
     where "from" = {{wallet_address}}
       and block_time >= now() - interval '{{days}}' day
     group by to_address
     order by tx_count desc
     limit 20
     ```

## Making Gemini "Smarter" at Tool Selection

`gemini_agent.py` contains `SYSTEM_INSTRUCTION` that already guides the model:
- Simple "check recent transactions/balances" → prioritize using the ready-made on-chain data interfaces (faster, less token usage);
- Questions involving aggregate statistics or complex time-window calculations → prioritize using run_dune_sql_query (provided the corresponding query_id exists).

You can continue to extend tools in `tools.py` based on your business needs, for example:
- `get_token_price`（token prices）
- `get_nft_holdings`（NFT holdings）
- A dedicated tool wrapping a Dune saved query for a specific high-frequency analysis scenario.

## Important Notes

- **Rate limits / Costs**：Both Dune and Gemini have their own API rate limits and usage-based pricing. In production, it is advisable to add caching and rate limiting to manage costs and avoid hitting quota ceilings.
- **Data volume control**：On-chain data can be extremely large. The code truncates responses（`rows[:200]`、JSON length truncation）to avoid pushing oversized data into Gemini's context. For more refined analysis, it's recommended to aggregate at the SQL level rather than passing all raw data to the model.
- **Dune API endpoints may change**：The on-chain data interface paths in `dune_client.py`（`api/echo/v1/...`）
  are reference implementations based on Dune's public documentation.Before actual use, please verify against the [Dune offical documentation](https://docs.dune.com/) to confirm the latest paths and field names, and adjust as necessary.
- **Security**：Do not commit `.env` to your git repository; be aware of API key leakage risks.