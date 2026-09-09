"""Backward-compatible entry point for the banking data model."""

from models.banking_model import DB_PATH, DUMMY_ACCOUNT_ID, DUMMY_USER_ID, create_database

__all__ = ["DB_PATH", "DUMMY_ACCOUNT_ID", "DUMMY_USER_ID", "create_database"]


if __name__ == "__main__":
    create_database()
    print(f"Created {DB_PATH}")
