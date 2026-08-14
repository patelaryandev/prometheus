import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.core.deps import get_current_user
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[CategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """List all categories for the current user."""
    result = await db.execute(
        select(Category).where(Category.user_id == current_user.id).order_by(Category.name)
    )
    categories = result.scalars().all()

    logger.info(f"User {current_user.email} listed {len(categories)} categories")
    return categories


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """Create a new category for the current user."""
    new_category = Category(
        user_id=current_user.id,
        name=category_data.name,
        monthly_limit=category_data.monthly_limit,
    )

    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)

    logger.info(f"User {current_user.email} created category: {new_category.name}")
    return new_category


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """Get a specific category by ID."""
    result = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == current_user.id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    logger.info(f"User {current_user.email} retrieved category: {category.name}")
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """Update a category."""
    result = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == current_user.id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Update fields if provided
    if category_data.name is not None:
        category.name = category_data.name
    if category_data.monthly_limit is not None:
        category.monthly_limit = category_data.monthly_limit

    await db.commit()
    await db.refresh(category)

    logger.info(f"User {current_user.email} updated category: {category.name}")
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """Delete a category."""
    result = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == current_user.id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    await db.delete(category)
    await db.commit()

    logger.info(f"User {current_user.email} deleted category: {category.name}")
