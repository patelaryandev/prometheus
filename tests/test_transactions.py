import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def register_and_login():
    """Helper to register and login a user, returns access token."""
    import random
    import string

    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    email = f"user_{suffix}@example.com"
    client.post("/auth/register", json={"email": email, "password": "password123"})
    response = client.post("/auth/login", data={"username": email, "password": "password123"})
    return response.json()["access_token"]


def create_category(token, name="Test Category", monthly_limit=None):
    """Helper to create a category and return its ID."""
    response = client.post(
        "/categories/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name, "monthly_limit": monthly_limit},
    )
    return response.json()["id"]


class TestTransactions:
    """Test transaction CRUD endpoints."""

    def test_create_transaction_success(self):
        """Test creating a transaction."""
        token = register_and_login()
        category_id = create_category(token, "Groceries")

        response = client.post(
            "/transactions/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "category_id": category_id,
                "amount": -50.75,
                "description": "Weekly shopping",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == -50.75
        assert data["description"] == "Weekly shopping"
        assert data["category_id"] == category_id
        assert "id" in data
        assert "occurred_at" in data

    def test_create_transaction_with_custom_date(self):
        """Test creating a transaction with custom occurred_at."""
        token = register_and_login()
        category_id = create_category(token, "Transport")

        custom_date = "2026-08-01T10:00:00"
        response = client.post(
            "/transactions/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "category_id": category_id,
                "amount": -25.00,
                "occurred_at": custom_date,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert custom_date in data["occurred_at"]

    def test_create_transaction_invalid_category(self):
        """Test creating transaction with non-existent category fails."""
        token = register_and_login()

        response = client.post(
            "/transactions/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "category_id": 99999,
                "amount": -10.00,
            },
        )
        assert response.status_code == 404

    def test_create_transaction_other_users_category(self):
        """Test creating transaction with another user's category fails."""
        token1 = register_and_login()
        token2 = register_and_login()

        # User 1 creates a category
        category_id = create_category(token1, "User1 Category")

        # User 2 tries to create transaction in User 1's category
        response = client.post(
            "/transactions/",
            headers={"Authorization": f"Bearer {token2}"},
            json={
                "category_id": category_id,
                "amount": -50.00,
            },
        )
        assert response.status_code == 404

    def test_create_transaction_unauthorized(self):
        """Test creating transaction without authentication fails."""
        response = client.post(
            "/transactions/",
            json={
                "category_id": 1,
                "amount": -10.00,
            },
        )
        assert response.status_code == 401

    def test_list_transactions(self):
        """Test listing transactions."""
        token = register_and_login()
        category_id = create_category(token, "Food")

        # Create multiple transactions
        for i in range(3):
            client.post(
                "/transactions/",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "category_id": category_id,
                    "amount": -(10.00 + i),
                    "description": f"Transaction {i}",
                },
            )

        # List transactions
        response = client.get("/transactions/", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_list_transactions_with_pagination(self):
        """Test transaction list pagination."""
        token = register_and_login()
        category_id = create_category(token, "Shopping")

        # Create 5 transactions
        for i in range(5):
            client.post(
                "/transactions/",
                headers={"Authorization": f"Bearer {token}"},
                json={"category_id": category_id, "amount": -(i + 1)},
            )

        # Get first 2
        response = client.get(
            "/transactions/?skip=0&limit=2", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Get next 2
        response = client.get(
            "/transactions/?skip=2&limit=2", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_transactions_filter_by_category(self):
        """Test filtering transactions by category."""
        token = register_and_login()
        category1 = create_category(token, "Food")
        category2 = create_category(token, "Transport")

        # Create transactions in different categories
        client.post(
            "/transactions/",
            headers={"Authorization": f"Bearer {token}"},
            json={"category_id": category1, "amount": -20},
        )
        client.post(
            "/transactions/",
            headers={"Authorization": f"Bearer {token}"},
            json={"category_id": category2, "amount": -15},
        )

        # Filter by category1
        response = client.get(
            f"/transactions/?category_id={category1}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert all(t["category_id"] == category1 for t in data)

    def test_get_transaction(self):
        """Test getting a specific transaction."""
        token = register_and_login()
        category_id = create_category(token, "Entertainment")

        # Create transaction
        create_response = client.post(
            "/transactions/",
            headers={"Authorization": f"Bearer {token}"},
            json={"category_id": category_id, "amount": -30.00, "description": "Movie tickets"},
        )
        transaction_id = create_response.json()["id"]

        # Get transaction
        response = client.get(
            f"/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Movie tickets"

    def test_get_transaction_not_found(self):
        """Test getting non-existent transaction."""
        token = register_and_login()
        response = client.get(
            "/transactions/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_update_transaction(self):
        """Test updating a transaction."""
        token = register_and_login()
        category_id = create_category(token, "Food")

        # Create transaction
        create_response = client.post(
            "/transactions/",
            headers={"Authorization": f"Bearer {token}"},
            json={"category_id": category_id, "amount": -25.00},
        )
        transaction_id = create_response.json()["id"]

        # Update transaction
        response = client.put(
            f"/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": -35.00, "description": "Updated description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == -35.00
        assert data["description"] == "Updated description"

    def test_delete_transaction(self):
        """Test deleting a transaction."""
        token = register_and_login()
        category_id = create_category(token, "Misc")

        # Create transaction
        create_response = client.post(
            "/transactions/",
            headers={"Authorization": f"Bearer {token}"},
            json={"category_id": category_id, "amount": -10.00},
        )
        transaction_id = create_response.json()["id"]

        # Delete transaction
        response = client.delete(
            f"/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(
            f"/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404

    def test_transaction_isolation_between_users(self):
        """Test that users can only access their own transactions."""
        token1 = register_and_login()
        token2 = register_and_login()

        category1 = create_category(token1, "User1 Category")

        # User 1 creates transaction
        create_response = client.post(
            "/transactions/",
            headers={"Authorization": f"Bearer {token1}"},
            json={"category_id": category1, "amount": -100.00},
        )
        transaction_id = create_response.json()["id"]

        # User 2 tries to access User 1's transaction
        response = client.get(
            f"/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404
