"""Banking data model and SQLite database initialization."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bank_data.db"
DUMMY_USER_ID = "USR-1001"
DUMMY_ACCOUNT_ID = "ACC-1001"


def create_database(db_path: Path = DB_PATH) -> None:
    """Create fresh, deterministic demo data for the banking assistant."""
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            DROP TABLE IF EXISTS accounts;
            DROP TABLE IF EXISTS transactions;
            DROP TABLE IF EXISTS service_requests;

            CREATE TABLE accounts (
                account_id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                account_type TEXT NOT NULL, holder_name TEXT NOT NULL,
                branch TEXT NOT NULL, balance REAL NOT NULL,
                currency TEXT NOT NULL, opened_on TEXT NOT NULL
            );
            CREATE TABLE transactions (
                transaction_id TEXT PRIMARY KEY, account_id TEXT NOT NULL,
                transaction_date TEXT NOT NULL, description TEXT NOT NULL,
                category TEXT NOT NULL, transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            );
            CREATE TABLE service_requests (
                request_id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                request_type TEXT NOT NULL, status TEXT NOT NULL,
                submitted_on TEXT NOT NULL, notes TEXT NOT NULL
            );
            """
        )
        connection.executemany("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            ("ACC-1001", DUMMY_USER_ID, "Checking", "Jordan Lee", "Seattle Downtown", 8420.55, "USD", "2021-04-19"),
            ("ACC-1002", DUMMY_USER_ID, "Savings", "Jordan Lee", "Seattle Downtown", 24650.00, "USD", "2022-09-03"),
            ("ACC-2001", "USR-1002", "Checking", "Morgan Patel", "Austin Central", 5100.25, "USD", "2020-11-28"),
            ("ACC-3001", "USR-1003", "Savings", "Taylor Kim", "Denver Union", 18750.75, "USD", "2023-01-14"),
            ("ACC-4001", "USR-1004", "Checking", "Casey Smith", "Boston Harbor", 3288.10, "USD", "2019-07-08"),
        ])
        connection.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("TXN-5001", "ACC-1001", "2026-08-02", "Grocery Market", "Groceries", "debit", 86.42),
            ("TXN-5002", "ACC-1001", "2026-08-05", "Payroll Deposit", "Income", "credit", 3250.00),
            ("TXN-5003", "ACC-1001", "2026-08-08", "Electric Utility", "Bills", "debit", 142.18),
            ("TXN-5004", "ACC-1001", "2026-08-12", "Coffee House", "Dining", "debit", 8.75),
            ("TXN-5005", "ACC-1001", "2026-08-16", "Online Transfer", "Transfer", "debit", 400.00),
            ("TXN-5006", "ACC-1002", "2026-08-10", "Monthly Interest", "Interest", "credit", 18.35),
            ("TXN-5007", "ACC-2001", "2026-08-11", "Fuel Station", "Transport", "debit", 55.20),
        ])
        connection.executemany("INSERT INTO service_requests VALUES (?, ?, ?, ?, ?, ?)", [
            ("SR-7001", DUMMY_USER_ID, "KYC update", "In review", "2026-08-18", "Identity document review requested."),
            ("SR-7002", DUMMY_USER_ID, "Cheque Book", "Completed", "2026-07-21", "25-leaf cheque book dispatched."),
            ("SR-7003", "USR-1002", "Change of Address", "Open", "2026-08-15", "Proof of address pending."),
            ("SR-7004", DUMMY_USER_ID, "Change of Address", "Open", "2026-08-19", "Awaiting confirmation."),
            ("SR-7005", "USR-1003", "Cheque Book", "Completed", "2026-06-11", "Cheque book delivered."),
        ])


if __name__ == "__main__":
    create_database()
    print(f"Created {DB_PATH}")
