import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.core.deps import get_current_user
from app.models.user import User
from app.services.analytics import get_monthly_summary

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary")
async def get_analytics_summary(
    year: int | None = Query(None, description="Year (defaults to current year)"),
    month: int | None = Query(None, ge=1, le=12, description="Month (defaults to current month)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """
    Get spending analytics summary for a specific month.

    Returns spend by category and budget status (remaining budget, percentage used).
    """
    # Default to current month if not specified
    now = datetime.utcnow()
    year = year or now.year
    month = month or now.month

    summary = await get_monthly_summary(current_user.id, year, month, db)

    logger.info(f"User {current_user.email} requested analytics for {year}-{month:02d}")
    return summary
