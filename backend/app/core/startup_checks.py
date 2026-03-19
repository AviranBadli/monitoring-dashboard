"""Startup checks to verify external dependencies are reachable"""

import logging
from typing import Tuple

import httpx
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

logger = logging.getLogger(__name__)


async def check_victoria_metrics() -> Tuple[bool, str]:
    """
    Check if Victoria Metrics endpoint is reachable

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.VICTORIA_METRICS_URL}/health")
            if response.status_code == 200:
                logger.info(f"✓ Victoria Metrics is reachable at {settings.VICTORIA_METRICS_URL}")
                return True, f"Victoria Metrics is reachable at {settings.VICTORIA_METRICS_URL}"
            else:
                error_msg = f"Victoria Metrics returned status code {response.status_code}"
                logger.error(f"✗ {error_msg}")
                return False, error_msg
    except httpx.ConnectError as e:
        error_msg = f"Cannot connect to Victoria Metrics at {settings.VICTORIA_METRICS_URL}: {e}"
        logger.error(f"✗ {error_msg}")
        return False, error_msg
    except httpx.TimeoutException:
        error_msg = f"Timeout connecting to Victoria Metrics at {settings.VICTORIA_METRICS_URL}"
        logger.error(f"✗ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Error checking Victoria Metrics: {e}"
        logger.error(f"✗ {error_msg}")
        return False, error_msg


def check_database() -> Tuple[bool, str]:
    """
    Check if PostgreSQL database is reachable

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Try to connect and execute a simple query
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        # Extract database name from URL for logging (without credentials)
        db_url = settings.DATABASE_URL
        if "@" in db_url:
            # Format: postgresql://user:pass@host:port/dbname
            host_part = db_url.split("@")[1]
            logger.info(f"✓ PostgreSQL Database is reachable at {host_part}")
            return True, f"PostgreSQLDatabase is reachable at {host_part}"
        else:
            logger.info("✓ PostgreSQLDatabase is reachable")
            return True, "PostgreSQLDatabase is reachable"

    except Exception as e:
        error_msg = f"Cannot connect to PostgreSQL database: {e}"
        logger.error(f"✗ {error_msg}")
        return False, error_msg


async def run_startup_checks() -> bool:
    """
    Run all startup checks

    Returns:
        True if all checks pass, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Running startup checks...")
    logger.info("=" * 60)

    # Log configured endpoints
    db_url = settings.DATABASE_URL
    if "@" in db_url:
        # Sanitize database URL to hide credentials
        # Format: postgresql://user:pass@host:port/dbname
        host_part = db_url.split("@")[1]
        logger.info(f"Database configured at: {host_part}")
    else:
        logger.info(f"Database configured at: {db_url}")

    logger.info(f"Victoria Metrics configured at: {settings.VICTORIA_METRICS_URL}")
    logger.info("")

    checks = []

    # Check database
    db_success, db_msg = check_database()
    checks.append(("Database", db_success, db_msg))

    # Check Victoria Metrics
    vm_success, vm_msg = await check_victoria_metrics()
    checks.append(("Victoria Metrics", vm_success, vm_msg))

    # Log results
    logger.info("=" * 60)
    logger.info("Startup check results:")
    for name, success, msg in checks:
        status = "PASS" if success else "FAIL"
        logger.info(f"  [{status}] {name}")

    all_passed = all(success for _, success, _ in checks)

    if all_passed:
        logger.info("=" * 60)
        logger.info("✓ All startup checks passed!")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("✗ Some startup checks failed!")
        logger.error("=" * 60)
        for name, success, msg in checks:
            if not success:
                logger.error(f"  {name}: {msg}")
        logger.error("=" * 60)

    return all_passed
