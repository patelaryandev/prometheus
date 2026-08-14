#!/usr/bin/env python3
"""
Budget alert check script.

Run this script on a schedule (daily or weekly) to check for budget limit violations
and send alerts.

Usage:
    python scripts/run_budget_check.py
    
Or with uv:
    uv run python scripts/run_budget_check.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.services.alerts import check_budget_alerts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run budget checks."""
    logger.info("Starting budget alert check...")

    if not settings.database_url:
        logger.error("DATABASE_URL is not configured. Cannot run budget check.")
        sys.exit(1)

    # Create database connection
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with async_session() as session:
            result = await check_budget_alerts(session)
            
            logger.info("Budget check completed successfully!")
            logger.info(f"Categories checked: {result['categories_checked']}")
            logger.info(f"Warnings sent (80%): {result['alerts_sent']['warning_80_percent']}")
            logger.info(f"Alerts sent (100%): {result['alerts_sent']['exceeded_100_percent']}")
            
    except Exception as e:
        logger.error(f"Error during budget check: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
