from datetime import datetime

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    """Schema for creating a transaction."""

    category_id: int
    amount: float = Field(..., description="Positive for income, negative for expenses")
    description: str | None = None
    occurred_at: datetime | None = None


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""

    category_id: int | None = None
    amount: float | None = Field(None, description="Positive for income, negative for expenses")
    description: str | None = None
    occurred_at: datetime | None = None


class TransactionResponse(BaseModel):
    """Schema for transaction response."""

    id: int
    user_id: int
    category_id: int
    amount: float
    description: str | None
    occurred_at: datetime

    model_config = {"from_attributes": True}
