import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.core.deps import get_current_user
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[TransactionResponse])
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """List transactions for the current user with optional filtering."""
    query = select(Transaction).where(Transaction.user_id == current_user.id)

    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)

    query = query.order_by(Transaction.occurred_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    transactions = result.scalars().all()

    logger.info(f"User {current_user.email} listed {len(transactions)} transactions")
    return transactions


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """Create a new transaction for the current user."""
    # Verify category belongs to user
    result = await db.execute(
        select(Category).where(
            Category.id == transaction_data.category_id, Category.user_id == current_user.id
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or does not belong to user",
        )

    new_transaction = Transaction(
        user_id=current_user.id,
        category_id=transaction_data.category_id,
        amount=transaction_data.amount,
        description=transaction_data.description,
        occurred_at=transaction_data.occurred_at or datetime.utcnow(),
    )

    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)

    logger.info(f"User {current_user.email} created transaction: ${new_transaction.amount}")
    return new_transaction


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """Get a specific transaction by ID."""
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id, Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    logger.info(f"User {current_user.email} retrieved transaction: {transaction.id}")
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """Update a transaction."""
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id, Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    # Verify category if being updated
    if transaction_data.category_id is not None:
        result = await db.execute(
            select(Category).where(
                Category.id == transaction_data.category_id, Category.user_id == current_user.id
            )
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or does not belong to user",
            )

        transaction.category_id = transaction_data.category_id

    # Update other fields if provided
    if transaction_data.amount is not None:
        transaction.amount = transaction_data.amount
    if transaction_data.description is not None:
        transaction.description = transaction_data.description
    if transaction_data.occurred_at is not None:
        transaction.occurred_at = transaction_data.occurred_at

    await db.commit()
    await db.refresh(transaction)

    logger.info(f"User {current_user.email} updated transaction: {transaction.id}")
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """Delete a transaction."""
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id, Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    await db.delete(transaction)
    await db.commit()

    logger.info(f"User {current_user.email} deleted transaction: {transaction.id}")
