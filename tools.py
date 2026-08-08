"""
Defines the tool definitions (function declarations) provided to Gemini,
along with the actual execution functions corresponding to each tool name (which actually invoke the Dune API).
"""
from dune_client import DuneClient

dune = DuneClient()

# ------------------------------------------------------------------
# 1. Gemini Tool Schema (OpenAPI style, the format required by Gemini function calling)
# ------------------------------------------------------------------
TOOLS = [
    {
        "function_declarations": [
            {
                "name": "run_dune_sql_query",
                "description": (
                    "Executes an SQL Query already created on the Dune web UI (referenced by query_id). "
                    "Suitable for user scenarios that require custom or complex on-chain statistics, such as "
                    "historical interaction counts for certain contracts, aggregated statistics over custom time ranges, "
                    "cross-table joins, etc. Requires knowing the corresponding query_id beforehand."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_id": {
                            "type": "integer",
                            "description": "The ID of the saved query on Dune",
                        },
                        "params": {
                            "type": "object",
                            "description": "Key-value pairs of parameters passed to the query (corresponding to {{parameter}} in the Dune query), can be an empty object",
                        },
                    },
                    "required": ["query_id"],
                },
            },
            {
                "name": "get_wallet_balances",
                "description": "Retrieves the current token balances held by a specified wallet address (spot holdings snapshot, not historical changes).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "address": {"type": "string", "description": "Wallet address, e.g., 0x..."},
                        "chain_ids": {
                            "type": "string",
                            "description": "Chain ID(s), e.g., '1' for Ethereum mainnet, '1,137' for querying both Ethereum and Polygon simultaneously. Default is '1'",
                        },
                    },
                    "required": ["address"],
                },
            },
            {
                "name": "get_wallet_transactions",
                "description": "Retrieves recent native transaction records (such as ETH transfers or contract calls) for a specified wallet address, which can be used to analyze recent activity, gas consumption, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "address": {"type": "string", "description": "Wallet address"},
                        "limit": {"type": "integer", "description": "Number of items to return, default 50"},
                    },
                    "required": ["address"],
                },
            },
            {
                "name": "get_token_transfers",
                "description": "Retrieves recent token transfer-in/transfer-out records (ERC20 / ERC721, etc.) for a specified wallet address, which can be used to analyze fund flows and counterparties.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "address": {"type": "string", "description": "Wallet address"},
                        "limit": {"type": "integer", "description": "Number of items to return, default 50"},
                    },
                    "required": ["address"],
                },
            },
        ]
    }
]


# ------------------------------------------------------------------
# 2. Tool Name -> Actual Execution Function (Step ③ Python calls the Dune API)
# ------------------------------------------------------------------
def _run_dune_sql_query(query_id: int, params: dict | None = None):
    rows = dune.run_query_and_wait(query_id, params or {})
    # Truncate the row count to prevent overly large datasets from blowing up Gemini's context window
    return {"row_count": len(rows), "rows": rows[:200]}


def _get_wallet_balances(address: str, chain_ids: str = "1"):
    return dune.get_wallet_balances(address, chain_ids)


def _get_wallet_transactions(address: str, limit: int = 50):
    return dune.get_wallet_transactions(address, limit)


def _get_token_transfers(address: str, limit: int = 50):
    return dune.get_token_transfers(address, limit)


TOOL_DISPATCH = {
    "run_dune_sql_query": _run_dune_sql_query,
    "get_wallet_balances": _get_wallet_balances,
    "get_wallet_transactions": _get_wallet_transactions,
    "get_token_transfers": _get_token_transfers,
}