from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """Schema for creating a category."""

    name: str = Field(..., min_length=1, max_length=100)
    monthly_limit: float | None = Field(None, ge=0)


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: str | None = Field(None, min_length=1, max_length=100)
    monthly_limit: float | None = Field(None, ge=0)


class CategoryResponse(BaseModel):
    """Schema for category response."""

    id: int
    user_id: int
    name: str
    monthly_limit: float | None

    model_config = {"from_attributes": True}
