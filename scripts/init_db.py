#!/usr/bin/env python3
"""
Database Initialization Script
Executes Alembic migrations up to head to create and update database schema.
(Uses Alembic migration mechanism as required for production)
"""

import logging
import os
import sys

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from alembic.config import Config
from alembic import command

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_migrations():
    """Apply Alembic migrations to upgrade database to head."""
    alembic_ini_path = os.path.join(backend_dir, "alembic.ini")
    logger.info(f"Loading Alembic configuration from {alembic_ini_path}...")
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))

    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    logger.info("Applying migrations (alembic upgrade head)...")
    command.upgrade(alembic_cfg, "head")
    logger.info("Database schema initialized and updated to head successfully via Alembic.")


if __name__ == "__main__":
    try:
        run_migrations()
    except Exception as e:
        logger.error(f"Failed to initialize database via migrations: {e}")
        sys.exit(1)
