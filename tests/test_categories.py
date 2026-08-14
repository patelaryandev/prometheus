import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def register_and_login():
    """Helper to register and login a user, returns access token."""
    email = f"user_{pytest.generate_random_email()}@example.com"
    client.post("/auth/register", json={"email": email, "password": "password123"})
    response = client.post("/auth/login", data={"username": email, "password": "password123"})
    return response.json()["access_token"]


class TestCategories:
    """Test category CRUD endpoints."""

    def test_create_category_success(self):
        """Test creating a category."""
        token = register_and_login()
        response = client.post(
            "/categories/",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Groceries", "monthly_limit": 500.00},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Groceries"
        assert data["monthly_limit"] == 500.00
        assert "id" in data
        assert "user_id" in data

    def test_create_category_without_limit(self):
        """Test creating a category without monthly limit."""
        token = register_and_login()
        response = client.post(
            "/categories/",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Entertainment"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Entertainment"
        assert data["monthly_limit"] is None

    def test_create_category_unauthorized(self):
        """Test creating category without authentication fails."""
        response = client.post(
            "/categories/",
            json={"name": "Groceries", "monthly_limit": 500.00},
        )
        assert response.status_code == 401

    def test_create_category_invalid_data(self):
        """Test creating category with invalid data fails."""
        token = register_and_login()
        response = client.post(
            "/categories/",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "", "monthly_limit": -100},  # Empty name, negative limit
        )
        assert response.status_code == 422

    def test_list_categories(self):
        """Test listing categories."""
        token = register_and_login()

        # Create some categories
        client.post(
            "/categories/",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Food", "monthly_limit": 300},
        )
        client.post(
            "/categories/",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Transport", "monthly_limit": 150},
        )

        # List categories
        response = client.get("/categories/", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert all("name" in cat for cat in data)

    def test_list_categories_isolation(self):
        """Test that users only see their own categories."""
        token1 = register_and_login()
        token2 = register_and_login()

        # User 1 creates a category
        client.post(
            "/categories/",
            headers={"Authorization": f"Bearer {token1}"},
            json={"name": "User1 Category"},
        )

        # User 2 should not see User 1's category
        response = client.get("/categories/", headers={"Authorization": f"Bearer {token2}"})
        data = response.json()
        assert all(cat["name"] != "User1 Category" for cat in data)

    def test_get_category(self):
        """Test getting a specific category."""
        token = register_and_login()

        # Create category
        create_response = client.post(
            "/categories/",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Healthcare", "monthly_limit": 200},
        )
        category_id = create_response.json()["id"]

        # Get category
        response = client.get(
            f"/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Healthcare"
        assert data["monthly_limit"] == 200

    def test_get_category_not_found(self):
        """Test getting non-existent category."""
        token = register_and_login()
        response = client.get(
            "/categories/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_get_category_unauthorized_access(self):
        """Test accessing another user's category."""
        token1 = register_and_login()
        token2 = register_and_login()

        # User 1 creates category
        create_response = client.post(
            "/categories/",
            headers={"Authorization": f"Bearer {token1}"},
            json={"name": "Private Category"},
        )
        category_id = create_response.json()["id"]

        # User 2 tries to access it
        response = client.get(
            f"/categories/{category_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404

    def test_update_category(self):
        """Test updating a category."""
        token = register_and_login()

        # Create category
        create_response = client.post(
            "/categories/",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Old Name", "monthly_limit": 100},
        )
        category_id = create_response.json()["id"]

        # Update category
        response = client.put(
            f"/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "New Name", "monthly_limit": 200},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["monthly_limit"] == 200

    def test_delete_category(self):
        """Test deleting a category."""
        token = register_and_login()

        # Create category
        create_response = client.post(
            "/categories/",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "To Delete"},
        )
        category_id = create_response.json()["id"]

        # Delete category
        response = client.delete(
            f"/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(
            f"/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404


# Helper for pytest - generate unique emails
@pytest.fixture(autouse=True)
def setup_unique_email(monkeypatch):
    """Setup unique email generation for tests."""
    import random
    import string

    def generate_email():
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return suffix

    monkeypatch.setattr(pytest, "generate_random_email", generate_email)
