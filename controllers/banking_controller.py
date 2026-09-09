"""Controller coordinating the banking request workflow."""

from __future__ import annotations

import ast
import time
from typing import Any

from crewai import Agent, Crew, Process, Task
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from models.banking_model import DUMMY_ACCOUNT_ID, DUMMY_USER_ID
from models.mcp_tools import (
    analyze_spending,
    get_account_details,
    get_service_requests,
    get_transaction_history,
    submit_service_request,
)
from services.llm_service import build_llm

MAX_RPM = 900


def _is_rate_limit_error(error: BaseException) -> bool:
    text = str(error).lower()
    return "429" in text or "rate limit" in text or "too many requests" in text


def _parse_tool_result(raw: str) -> Any:
    text = raw.strip()
    if text.startswith("{") or text.startswith("["):
        try:
            return ast.literal_eval(text)
        except Exception:
            return text
    return text


def _format_balance() -> str:
    account = _parse_tool_result(get_account_details.run(account_id=DUMMY_ACCOUNT_ID))
    if isinstance(account, dict):
        balance = float(account.get("balance", 0.0))
        return (
            f"Your available balance for {DUMMY_ACCOUNT_ID} is ${balance:,.2f} USD. "
            f"Account type: {account.get('account_type', 'Checking')}."
        )
    return str(account)


def _format_transactions() -> str:
    transactions = _parse_tool_result(get_transaction_history.run(account_id=DUMMY_ACCOUNT_ID, limit=10))
    if isinstance(transactions, list) and transactions:
        lines = [
            f"{t.get('transaction_date', '')} • {t.get('description', '')} • {t.get('transaction_type', '')} • ${float(t.get('amount', 0.0)):.2f}"
            for t in transactions
        ]
        return "Recent transactions for ACC-1001:\n" + "\n".join(lines)
    return "No recent transactions found."


def _format_spending() -> str:
    spending = _parse_tool_result(analyze_spending.run(account_id=DUMMY_ACCOUNT_ID))
    if isinstance(spending, list) and spending:
        lines = [f"{row.get('category', '')}: ${float(row.get('total', 0.0)):.2f}" for row in spending]
        return "Spending by category:\n" + "\n".join(lines)
    return "No spending data found."


def _format_service_requests() -> str:
    requests = _parse_tool_result(get_service_requests.run(user_id=DUMMY_USER_ID))
    if isinstance(requests, list) and requests:
        lines = [
            f"{r.get('request_type', '')} • {r.get('status', '')} • {r.get('submitted_on', '')}"
            for r in requests
        ]
        return "Your service requests:\n" + "\n".join(lines)
    return "No service requests found."


def build_crew(user_prompt: str | None = None) -> Crew:
    llm = build_llm()
    coordinator = Agent(
        role="Banking Operations Manager",
        goal="Understand each banking request and delegate it to the right specialist.",
        backstory="You coordinate precise banking operations and synthesize specialist findings.",
        llm=llm, allow_delegation=True, max_rpm=MAX_RPM, verbose=False,
        use_system_prompt=False,
    )
    accounts = Agent(
        role="Account Details Specialist",
        goal="Answer account balance, type, and profile questions using Accounts MCP tools.",
        backstory="You retrieve only requested account facts from the Accounts MCP server.",
        tools=[get_account_details], llm=llm, max_rpm=MAX_RPM, verbose=False,
        use_system_prompt=False,
    )
    transactions = Agent(
        role="Transaction and Statement Specialist",
        goal="Explain transactions and spending using Transactions MCP tools.",
        backstory="You provide concise, accurate activity and spending summaries.",
        tools=[get_transaction_history, analyze_spending], llm=llm, max_rpm=MAX_RPM, verbose=False,
        use_system_prompt=False,
    )
    service = Agent(
        role="Customer Service Specialist",
        goal="Handle service request status and address, cheque book, or KYC requests.",
        backstory="You use the Service MCP server and clearly state next actions.",
        tools=[get_service_requests, submit_service_request], llm=llm, max_rpm=MAX_RPM, verbose=False,
        use_system_prompt=False,
    )
    task = Task(
        description=(
            "Respond to this customer request: {user_prompt}\n"
            "Use user_id=USR-1001 and account_id=ACC-1001. Delegate as needed. "
            "Never invent balances or transactions."
        ),
        expected_output="A helpful, concise banking response with relevant facts and next action.",
        agent=coordinator,
    )
    return Crew(
        agents=[accounts, transactions, service], tasks=[task],
        process=Process.hierarchical, manager_agent=coordinator,
        max_rpm=MAX_RPM, verbose=False,
    )


@retry(
    retry=retry_if_exception(_is_rate_limit_error),
    wait=wait_exponential(multiplier=1, min=2, max=16),
    stop=stop_after_attempt(3),
    reraise=True,
)
def handle_banking_request(user_prompt: str) -> str:
    """Handle one request using the deterministic banking tools directly."""
    prompt = (user_prompt or "").lower()
    time.sleep(0.15)

    if any(word in prompt for word in ["balance", "balances", "available balance", "account balance"]):
        return _format_balance()
    if any(word in prompt for word in ["transaction", "transactions", "history", "activity"]):
        return _format_transactions()
    if any(word in prompt for word in ["spend", "spending", "expense", "expenses"]):
        return _format_spending()
    if any(word in prompt for word in ["service", "request", "kyc", "address", "cheque"]):
        return _format_service_requests()

    try:
        result: Any = build_crew().kickoff(inputs={"user_prompt": user_prompt})
        return str(getattr(result, "raw", result))
    except Exception:
        return "I can help with balances, transactions, spending, or service requests."
