import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


async def get_monthly_summary(user_id: int, year: int, month: int, db: AsyncSession) -> dict:
    """
    Get spending summary by category for a specific month.

    Returns:
        dict: Summary with spend_by_category and budget_status
    """
    # Get start and end of month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Query transactions grouped by category
    query = (
        select(
            Transaction.category_id,
            Category.name.label("category_name"),
            Category.monthly_limit,
            func.sum(Transaction.amount).label("total_spent"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at < end_date,
        )
        .group_by(Transaction.category_id, Category.name, Category.monthly_limit)
    )

    result = await db.execute(query)
    category_data = result.all()

    # Build response
    spend_by_category = []
    budget_status = []

    for row in category_data:
        category_id, category_name, monthly_limit, total_spent, transaction_count = row

        spend_by_category.append(
            {
                "category_id": category_id,
                "category_name": category_name,
                "total_spent": float(total_spent) if total_spent else 0.0,
                "transaction_count": transaction_count,
            }
        )

        # Calculate budget status if limit is set
        if monthly_limit is not None:
            spent = float(total_spent) if total_spent else 0.0
            limit = float(monthly_limit)
            remaining = limit - spent
            percentage_used = (spent / limit * 100) if limit > 0 else 0

            budget_status.append(
                {
                    "category_id": category_id,
                    "category_name": category_name,
                    "monthly_limit": limit,
                    "total_spent": spent,
                    "remaining_budget": remaining,
                    "percentage_used": round(percentage_used, 2),
                }
            )

    logger.info(f"Generated monthly summary for user {user_id}: {year}-{month:02d}")

    return {
        "period": {"year": year, "month": month},
        "spend_by_category": spend_by_category,
        "budget_status": budget_status,
    }
