"""SQLite-backed model operations exposed as simulated MCP tools."""

from __future__ import annotations

import sqlite3
from typing import Any

from crewai.tools import tool
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from models.banking_model import DB_PATH, DUMMY_ACCOUNT_ID, DUMMY_USER_ID, create_database


def _is_rate_limit_error(error: BaseException) -> bool:
    text = str(error).lower()
    return "429" in text or "rate limit" in text or "too many requests" in text


_RETRY = dict(
    retry=retry_if_exception(_is_rate_limit_error),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    stop=stop_after_attempt(3),
    reraise=True,
)


def _rows(query: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    if not DB_PATH.exists():
        create_database()
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(query, parameters).fetchall()]


@tool("get_account_details")
@retry(**_RETRY)
def get_account_details(account_id: str = DUMMY_ACCOUNT_ID) -> str:
    """Accounts MCP endpoint: retrieve account details."""
    records = _rows("SELECT * FROM accounts WHERE account_id = ?", (account_id,))
    return str(records[0] if records else {"error": "Account not found"})


@tool("get_transaction_history")
@retry(**_RETRY)
def get_transaction_history(account_id: str = DUMMY_ACCOUNT_ID, limit: int = 10) -> str:
    """Transactions MCP endpoint: retrieve recent transactions."""
    records = _rows(
        """SELECT transaction_date, description, category, transaction_type, amount
           FROM transactions WHERE account_id = ? ORDER BY transaction_date DESC LIMIT ?""",
        (account_id, max(1, min(limit, 50))),
    )
    return str(records)


@tool("analyze_spending")
@retry(**_RETRY)
def analyze_spending(account_id: str = DUMMY_ACCOUNT_ID) -> str:
    """Transactions MCP endpoint: summarize debit spending by category."""
    records = _rows(
        """SELECT category, ROUND(SUM(amount), 2) AS total
           FROM transactions WHERE account_id = ? AND transaction_type = 'debit'
           GROUP BY category ORDER BY total DESC""",
        (account_id,),
    )
    return str(records)


@tool("get_service_requests")
@retry(**_RETRY)
def get_service_requests(user_id: str = DUMMY_USER_ID) -> str:
    """Service MCP endpoint: list customer service requests."""
    return str(_rows("SELECT * FROM service_requests WHERE user_id = ? ORDER BY submitted_on DESC", (user_id,)))


@tool("submit_service_request")
@retry(**_RETRY)
def submit_service_request(request_type: str, notes: str = "") -> str:
    """Service MCP endpoint: create an address, cheque book, or KYC request."""
    allowed = {"Change of Address", "Cheque Book", "KYC update"}
    if request_type not in allowed:
        return f"Unsupported request type. Choose one of: {', '.join(sorted(allowed))}."
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO service_requests VALUES (?, ?, ?, ?, date('now'), ?)",
            ("SR-DEMO-NEW", DUMMY_USER_ID, request_type, "Open", notes or "Submitted by banking assistant."),
        )
    return f"Request SR-DEMO-NEW created for {request_type}."
