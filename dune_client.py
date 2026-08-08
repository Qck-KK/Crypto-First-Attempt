"""
Dune Analytics API Wrapper

Documentation: https://docs.dune.com/api-reference/overview/introduction

⚠️ Note: Dune's API endpoints and product formats are subject to periodic changes 
(e.g., Echo/Sim API paths, parameter naming, etc.). It is recommended to verify 
URLs and field names against the latest official Dune documentation before use.
The implementation in this file is written based on public documentation around 2025, 
serving as a runnable reference skeleton.
"""
import time
from typing import Optional

import requests

from config import DUNE_API_KEY

BASE_URL = "https://api.dune.com/api/v1"
# Dune's on-chain balance/transaction/transfer data endpoints (formerly Echo / Sim API)
ECHO_BASE_URL = "https://api.dune.com/api/echo/v1"


class DuneClient:
    def __init__(self, api_key: str = DUNE_API_KEY):
        self.headers = {"X-Dune-API-Key": api_key}

    # ---------------------------------------------------------------
    # 1. Custom SQL Query: Requires writing and saving SQL on the Dune web UI first to get a query_id.
    #    This is the most flexible approach, suitable for complex/custom statistical requirements.
    # ---------------------------------------------------------------
    def execute_query(self, query_id: int, params: Optional[dict] = None) -> str:
        """Triggers a query execution and returns the execution_id."""
        url = f"{BASE_URL}/query/{query_id}/execute"
        payload = {}
        if params:
            payload["query_parameters"] = params
        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["execution_id"]

    def get_execution_status(self, execution_id: str) -> dict:
        url = f"{BASE_URL}/execution/{execution_id}/status"
        resp = requests.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_execution_results(self, execution_id: str) -> dict:
        url = f"{BASE_URL}/execution/{execution_id}/results"
        resp = requests.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def run_query_and_wait(
        self,
        query_id: int,
        params: Optional[dict] = None,
        poll_interval: float = 2.0,
        timeout: float = 120.0,
    ) -> list:
        """Executes the query, polls until completion, and returns the result rows (list[dict])."""
        execution_id = self.execute_query(query_id, params)
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_execution_status(execution_id)
            state = status.get("state")
            if state == "QUERY_STATE_COMPLETED":
                result = self.get_execution_results(execution_id)
                return result.get("result", {}).get("rows", [])
            if state in ("QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"):
                raise RuntimeError(f"Dune query execution failed: {status}")
            time.sleep(poll_interval)
        raise TimeoutError("Dune query execution timed out")

    # ---------------------------------------------------------------
    # 2. Direct calls to Dune's on-chain data endpoints (no custom SQL needed, faster response)
    # ---------------------------------------------------------------
    def get_wallet_balances(self, address: str, chain_ids: str = "1") -> dict:
        """Retrieves the current token balance snapshot for a wallet. chain_ids examples: '1' (Ethereum), '1,137' (multi-chain)."""
        url = f"{ECHO_BASE_URL}/balances/evm/{address}"
        resp = requests.get(
            url, headers=self.headers, params={"chain_ids": chain_ids}, timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    def get_wallet_transactions(self, address: str, limit: int = 50) -> dict:
        """Retrieves recent native transactions (transfers / contract calls) for a wallet."""
        url = f"{ECHO_BASE_URL}/transactions/evm/{address}"
        resp = requests.get(
            url, headers=self.headers, params={"limit": limit}, timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    def get_token_transfers(self, address: str, limit: int = 50) -> dict:
        """Retrieves recent token transfer-in/transfer-out records for a wallet."""
        url = f"{ECHO_BASE_URL}/transfers/evm/{address}"
        resp = requests.get(
            url, headers=self.headers, params={"limit": limit}, timeout=30
        )
        resp.raise_for_status()
        return resp.json()