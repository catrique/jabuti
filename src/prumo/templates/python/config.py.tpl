"""Application settings read from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL

# Only the application's own .env is read; parent directories are ignored.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def database_url() -> URL:
    """Build the MySQL connection URL; credentials never live in code."""
    return URL.create(
        "mysql+pymysql",
        username=os.getenv("DB_USER") or None,
        password=os.getenv("DB_PASSWORD") or None,
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME") or None,
    )
