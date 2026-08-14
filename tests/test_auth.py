import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAuth:
    """Test authentication endpoints."""

    def test_register_user_success(self):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "securepassword123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails."""
        # Register first user
        client.post(
            "/auth/register",
            json={"email": "duplicate@example.com", "password": "password123"},
        )

        # Try to register again with same email
        response = client.post(
            "/auth/register",
            json={"email": "duplicate@example.com", "password": "different456"},
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self):
        """Test registration with invalid email format fails."""
        response = client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422  # Validation error

    def test_login_success(self):
        """Test successful login."""
        # Register user
        client.post(
            "/auth/register",
            json={"email": "login@example.com", "password": "mypassword123"},
        )

        # Login
        response = client.post(
            "/auth/login",
            data={"username": "login@example.com", "password": "mypassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        """Test login with wrong password fails."""
        # Register user
        client.post(
            "/auth/register",
            json={"email": "wrongpass@example.com", "password": "correctpass"},
        )

        # Try to login with wrong password
        response = client.post(
            "/auth/login",
            data={"username": "wrongpass@example.com", "password": "wrongpass"},
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self):
        """Test login with non-existent user fails."""
        response = client.post(
            "/auth/login",
            data={"username": "nobody@example.com", "password": "password123"},
        )
        assert response.status_code == 401

    def test_protected_route_without_token(self):
        """Test accessing protected route without token fails."""
        response = client.get("/categories/")
        assert response.status_code == 401

    def test_protected_route_with_invalid_token(self):
        """Test accessing protected route with invalid token fails."""
        response = client.get(
            "/categories/",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert response.status_code == 401
