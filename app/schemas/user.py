from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""

    username: EmailStr  # OAuth2 requires 'username' field
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for decoded token data."""

    email: str | None = None
