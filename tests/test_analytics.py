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


def create_category(token, name, monthly_limit=None):
    """Helper to create a category and return its ID."""
    response = client.post(
        "/categories/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name, "monthly_limit": monthly_limit},
    )
    return response.json()["id"]


def create_transaction(token, category_id, amount, occurred_at=None):
    """Helper to create a transaction."""
    payload = {"category_id": category_id, "amount": amount}
    if occurred_at:
        payload["occurred_at"] = occurred_at
    response = client.post(
        "/transactions/",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    return response.json()


class TestAnalytics:
    """Test analytics endpoints."""

    def test_analytics_summary_empty(self):
        """Test analytics summary with no transactions."""
        token = register_and_login()

        response = client.get("/analytics/summary", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "spend_by_category" in data
        assert "budget_status" in data
        assert len(data["spend_by_category"]) == 0
        assert len(data["budget_status"]) == 0

    def test_analytics_summary_with_transactions(self):
        """Test analytics summary with transactions."""
        token = register_and_login()

        # Create categories
        food_cat = create_category(token, "Food", 300.00)
        transport_cat = create_category(token, "Transport", 150.00)

        # Create transactions in current month
        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%dT%H:%M:%S")

        create_transaction(token, food_cat, -50.00, date_str)
        create_transaction(token, food_cat, -75.50, date_str)
        create_transaction(token, transport_cat, -30.00, date_str)

        # Get analytics
        response = client.get("/analytics/summary", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()

        # Check period
        assert data["period"]["year"] == now.year
        assert data["period"]["month"] == now.month

        # Check spend by category
        spend = data["spend_by_category"]
        assert len(spend) == 2

        food_spend = next((s for s in spend if s["category_name"] == "Food"), None)
        assert food_spend is not None
        assert food_spend["total_spent"] == 125.50
        assert food_spend["transaction_count"] == 2

        transport_spend = next((s for s in spend if s["category_name"] == "Transport"), None)
        assert transport_spend is not None
        assert transport_spend["total_spent"] == 30.00

        # Check budget status
        budget = data["budget_status"]
        assert len(budget) == 2

        food_budget = next((b for b in budget if b["category_name"] == "Food"), None)
        assert food_budget is not None
        assert food_budget["monthly_limit"] == 300.00
        assert food_budget["total_spent"] == 125.50
        assert food_budget["remaining_budget"] == 174.50
        assert food_budget["percentage_used"] > 0

    def test_analytics_summary_specific_month(self):
        """Test analytics summary for a specific month."""
        token = register_and_login()
        category_id = create_category(token, "Shopping", 500.00)

        # Create transaction in August 2026
        create_transaction(token, category_id, -100.00, "2026-08-15T10:00:00")

        # Create transaction in July 2026
        create_transaction(token, category_id, -200.00, "2026-07-15T10:00:00")

        # Get August analytics
        response = client.get(
            "/analytics/summary?year=2026&month=8",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["period"]["year"] == 2026
        assert data["period"]["month"] == 8

        # Should only show August transaction
        spend = data["spend_by_category"]
        assert len(spend) == 1
        assert spend[0]["total_spent"] == 100.00

        # Get July analytics
        response = client.get(
            "/analytics/summary?year=2026&month=7",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["period"]["month"] == 7
        assert data["spend_by_category"][0]["total_spent"] == 200.00

    def test_analytics_budget_percentage_calculation(self):
        """Test budget percentage calculation."""
        token = register_and_login()
        category_id = create_category(token, "Groceries", 100.00)

        # Spend exactly 80% of budget
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        create_transaction(token, category_id, -80.00, now)

        response = client.get("/analytics/summary", headers={"Authorization": f"Bearer {token}"})
        data = response.json()

        budget_status = data["budget_status"][0]
        assert budget_status["percentage_used"] == 80.00
        assert budget_status["remaining_budget"] == 20.00

    def test_analytics_category_without_limit(self):
        """Test analytics for category without monthly limit."""
        token = register_and_login()
        category_id = create_category(token, "No Limit Category", None)

        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        create_transaction(token, category_id, -50.00, now)

        response = client.get("/analytics/summary", headers={"Authorization": f"Bearer {token}"})
        data = response.json()

        # Should appear in spend_by_category
        spend = data["spend_by_category"]
        assert len(spend) == 1
        assert spend[0]["total_spent"] == 50.00

        # Should NOT appear in budget_status (no limit set)
        budget = data["budget_status"]
        assert len(budget) == 0

    def test_analytics_unauthorized(self):
        """Test analytics endpoint without authentication."""
        response = client.get("/analytics/summary")
        assert response.status_code == 401

    def test_analytics_user_isolation(self):
        """Test that users only see their own analytics."""
        token1 = register_and_login()
        token2 = register_and_login()

        # User 1 creates category and transaction
        cat1 = create_category(token1, "User1 Category", 100.00)
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        create_transaction(token1, cat1, -50.00, now)

        # User 2 should see empty analytics
        response = client.get("/analytics/summary", headers={"Authorization": f"Bearer {token2}"})
        data = response.json()
        assert len(data["spend_by_category"]) == 0
        assert len(data["budget_status"]) == 0

    def test_analytics_invalid_month(self):
        """Test analytics with invalid month parameter."""
        token = register_and_login()

        response = client.get(
            "/analytics/summary?month=13",  # Invalid month
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422  # Validation error
