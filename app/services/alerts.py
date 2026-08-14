import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class EmailService:
    """
    Stub email service for budget alerts.
    
    In production, integrate with SendGrid, AWS SES, or similar service.
    """

    @staticmethod
    def send_alert(user_email: str, subject: str, message: str) -> None:
        """
        Send an email alert.
        
        Currently logs the alert. Replace with actual email implementation.
        """
        logger.info(f"[EMAIL ALERT] To: {user_email}")
        logger.info(f"[EMAIL ALERT] Subject: {subject}")
        logger.info(f"[EMAIL ALERT] Message: {message}")


async def check_budget_alerts(db: AsyncSession) -> dict:
    """
    Check all categories with monthly limits and identify those exceeding thresholds.
    
    Returns:
        dict: Summary of alerts sent with counts for 80% and 100% thresholds
    """
    # Get current month boundaries
    now = datetime.utcnow()
    start_date = datetime(now.year, now.month, 1)
    if now.month == 12:
        end_date = datetime(now.year + 1, 1, 1)
    else:
        end_date = datetime(now.year, now.month + 1, 1)

    # Query categories with limits and their spending
    query = (
        select(
            Category.id,
            Category.name,
            Category.user_id,
            Category.monthly_limit,
            func.coalesce(func.sum(Transaction.amount), 0).label("total_spent"),
        )
        .outerjoin(
            Transaction,
            (Transaction.category_id == Category.id)
            & (Transaction.occurred_at >= start_date)
            & (Transaction.occurred_at < end_date),
        )
        .where(Category.monthly_limit.isnot(None))
        .group_by(Category.id, Category.name, Category.user_id, Category.monthly_limit)
    )

    result = await db.execute(query)
    categories_with_spending = result.all()

    alerts_80 = 0
    alerts_100 = 0
    email_service = EmailService()

    for row in categories_with_spending:
        category_id, category_name, user_id, monthly_limit, total_spent = row

        limit = float(monthly_limit)
        spent = float(total_spent)
        percentage_used = (spent / limit * 100) if limit > 0 else 0

        # Get user email (in production, fetch from database)
        user_email = f"user_{user_id}@example.com"  # Placeholder

        # Check thresholds
        if percentage_used >= 100:
            alerts_100 += 1
            subject = f"⚠️ Budget Exceeded: {category_name}"
            message = (
                f"Your category '{category_name}' has exceeded its monthly budget!\n"
                f"Budget: ${limit:.2f}\n"
                f"Spent: ${spent:.2f}\n"
                f"Over by: ${spent - limit:.2f}"
            )
            email_service.send_alert(user_email, subject, message)
            logger.warning(
                f"Category {category_id} ({category_name}) EXCEEDED budget: "
                f"${spent:.2f} / ${limit:.2f} ({percentage_used:.1f}%)"
            )

        elif percentage_used >= 80:
            alerts_80 += 1
            subject = f"⚠️ Budget Warning: {category_name}"
            message = (
                f"Your category '{category_name}' has reached {percentage_used:.1f}% of its monthly budget.\n"
                f"Budget: ${limit:.2f}\n"
                f"Spent: ${spent:.2f}\n"
                f"Remaining: ${limit - spent:.2f}"
            )
            email_service.send_alert(user_email, subject, message)
            logger.warning(
                f"Category {category_id} ({category_name}) at {percentage_used:.1f}% of budget: "
                f"${spent:.2f} / ${limit:.2f}"
            )

    logger.info(f"Budget check complete: {alerts_80} warnings at 80%, {alerts_100} exceeded at 100%")

    return {
        "timestamp": now.isoformat(),
        "alerts_sent": {
            "warning_80_percent": alerts_80,
            "exceeded_100_percent": alerts_100,
        },
        "categories_checked": len(categories_with_spending),
    }
