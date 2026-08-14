# Expense & Budget Tracker API

A production-ready FastAPI application for tracking expenses and managing budgets. Track spending across categories, set monthly limits, and receive alerts when approaching budget thresholds. Built with async SQLAlchemy, JWT authentication, and comprehensive testing.

**🚀 [Live Demo](https://expense-tracker-api-XXXX.onrender.com/docs)** | [API Health](https://expense-tracker-api-XXXX.onrender.com/health)

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         Expense Tracker API                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Auth      │  │ Categories  │  │Transactions │         │
│  │  /auth/*    │  │/categories/*│  │/transactions│         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                  │
│         └────────────────┴────────────────┘                  │
│                          │                                    │
│                  ┌───────▼────────┐                          │
│                  │  Services Layer │                          │
│                  │  - Analytics    │                          │
│                  │  - Alerts       │                          │
│                  └───────┬─────────┘                          │
│                          │                                    │
│                  ┌───────▼────────┐                          │
│                  │ SQLAlchemy ORM  │                          │
│                  │  Async Engine   │                          │
│                  └───────┬─────────┘                          │
│                          │                                    │
│                  ┌───────▼────────┐                          │
│                  │   PostgreSQL    │                          │
│                  │   (or SQLite)   │                          │
│                  └─────────────────┘                          │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│  Observability: Prometheus metrics, Sentry error tracking    │
└──────────────────────────────────────────────────────────────┘
```

---

## Features

- **JWT Authentication**: Secure user registration and login with bcrypt password hashing
- **Category Management**: Create spending categories with optional monthly budget limits
- **Transaction Tracking**: Record expenses and income with timestamps and descriptions
- **Analytics Dashboard**: View spend-by-category and budget status for any month
- **Budget Alerts**: Scheduled job checks for 80% and 100% budget threshold violations
- **Production Ready**: Includes Prometheus metrics, Sentry integration, and comprehensive tests
- **Async Everything**: Built on async/await with SQLAlchemy async and FastAPI

---

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| **Authentication** |
| POST | `/auth/register` | Register a new user | ❌ |
| POST | `/auth/login` | Login and get JWT token | ❌ |
| **Categories** |
| GET | `/categories/` | List user's categories | ✅ |
| POST | `/categories/` | Create a category | ✅ |
| GET | `/categories/{id}` | Get category by ID | ✅ |
| PUT | `/categories/{id}` | Update category | ✅ |
| DELETE | `/categories/{id}` | Delete category | ✅ |
| **Transactions** |
| GET | `/transactions/` | List user's transactions (with pagination & filters) | ✅ |
| POST | `/transactions/` | Create a transaction | ✅ |
| GET | `/transactions/{id}` | Get transaction by ID | ✅ |
| PUT | `/transactions/{id}` | Update transaction | ✅ |
| DELETE | `/transactions/{id}` | Delete transaction | ✅ |
| **Analytics** |
| GET | `/analytics/summary` | Get spending summary and budget status | ✅ |
| **Health** |
| GET | `/health/` | Basic health check | ❌ |
| GET | `/health/ready` | Readiness check (includes DB) | ❌ |
| GET | `/metrics` | Prometheus metrics | ❌ |

---

## Setup Instructions

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- PostgreSQL (or SQLite for development)

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <your-repo-url>
cd prometheus

# Install with uv (recommended)
make install

# Or with pip
pip install -r requirements.txt -r requirements-dev.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# Application
APP_NAME=Expense Tracker API
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/expense_tracker
# Or for SQLite: sqlite+aiosqlite:///./expense_tracker.db

# Security
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Optional: Sentry
SENTRY_DSN=your-sentry-dsn-here
```

### 3. Run Database Migrations

```bash
# Run migrations
make migrate

# Or manually
uv run alembic upgrade head
```

### 4. Start the Development Server

```bash
# Start with auto-reload
make dev

# Or manually
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI): `http://localhost:8000/docs`

### 5. Run Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
uv run pytest tests/test_auth.py -v

# Run with coverage report
uv run pytest --cov=app --cov-report=html
```

---

## Usage Example

### 1. Register a user

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'
```

### 2. Login and get token

```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=user@example.com&password=securepass123"

# Response: {"access_token": "eyJ...", "token_type": "bearer"}
```

### 3. Create a category

```bash
curl -X POST http://localhost:8000/categories/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Groceries", "monthly_limit": 500.00}'
```

### 4. Record a transaction

```bash
curl -X POST http://localhost:8000/transactions/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": 1,
    "amount": -45.50,
    "description": "Weekly shopping"
  }'
```

### 5. View analytics

```bash
curl -X GET "http://localhost:8000/analytics/summary?year=2026&month=8" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Scheduled Budget Alerts

The project includes a budget alert system that checks for spending thresholds:

```bash
# Run manually
uv run python scripts/run_budget_check.py
```

For production deployment on **Render**, add a cron job to your `render.yaml`:

```yaml
- type: cron
  name: budget-alert-checker
  schedule: "0 9 * * *"  # Daily at 9 AM UTC
  dockerCommand: uv run python scripts/run_budget_check.py
```

See [SCHEDULED_JOBS.md](SCHEDULED_JOBS.md) for detailed setup instructions.

---

## Database Migrations

```bash
# Create a new migration
make migrate-create msg="add new field"

# Apply migrations
make migrate

# Rollback one migration
make migrate-downgrade
```

---

## Design Decisions

### Why JWT over Sessions?

**JWT (JSON Web Tokens)** provides stateless authentication ideal for modern APIs:

- **Scalability**: No server-side session storage required, making horizontal scaling trivial
- **Mobile-friendly**: Tokens can be stored in mobile apps without cookie complexity
- **Microservices**: Tokens can be validated by multiple services without shared state
- **Decentralized**: No database lookup needed on every request

Trade-off: Cannot instantly revoke tokens (must wait for expiration). For this use case, 30-minute expiry provides a good balance.

### Why Service Layer Separation?

The architecture separates **route handlers** (`app/api/routes/`) from **business logic** (`app/services/`):

- **Testability**: Business logic can be tested independently of HTTP layer
- **Reusability**: Analytics service used by both API endpoint and alert script
- **Maintainability**: Clear separation of concerns makes codebase easier to navigate
- **Future-proofing**: Same services can power CLI tools, background jobs, or GraphQL resolvers

This is overkill for tiny projects but demonstrates production patterns for portfolio/interview purposes.

### Why Alembic?

**Alembic** is SQLAlchemy's migration tool, chosen because:

- **Version Control for Schema**: Every schema change is tracked in code
- **Reproducible Deployments**: Same migrations run identically across dev/staging/prod
- **Team Collaboration**: No merge conflicts from ad-hoc schema changes
- **Rollback Support**: Can revert schema changes when deployments fail
- **Autogenerate**: Can detect model changes and generate migrations automatically

Alternative approaches like `.create_all()` work for prototypes but don't scale to team environments.

---

## Deployment

### Deploy to Render

1. Push your code to GitHub
2. Create a new Web Service on [Render](https://render.com)
3. Connect your repository
4. Render will automatically detect `render.yaml` and set up:
   - PostgreSQL database
   - Web service with Docker
   - Environment variables
5. Add the cron job for budget alerts (see `SCHEDULED_JOBS.md`)

### Environment Variables on Render

Set these in the Render dashboard:

- `DATABASE_URL` - Auto-configured from PostgreSQL service
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `ENVIRONMENT` - Set to `production`
- `DEBUG` - Set to `false`
- `SENTRY_DSN` - (Optional) Your Sentry project DSN

---

## Development Commands

```bash
make help              # Show all available commands
make install           # Install dependencies with uv
make dev               # Run development server
make test              # Run tests with coverage
make lint              # Run code linting
make format            # Format code with ruff
make migrate           # Run database migrations
make migrate-create    # Create new migration
make docker-build      # Build Docker image
make docker-run        # Run in Docker
```

---

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL (production) / SQLite (development)
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose) + bcrypt (passlib)
- **Testing**: pytest + pytest-asyncio + pytest-cov
- **Linting**: Ruff
- **Monitoring**: Prometheus + Sentry
- **Deployment**: Docker + Render

---

## Project Structure

```
.
├── app/
│   ├── api/
│   │   └── routes/          # API endpoint handlers
│   │       ├── auth.py      # Authentication
│   │       ├── categories.py
│   │       ├── transactions.py
│   │       └── analytics.py
│   ├── core/
│   │   ├── database.py      # Database connection
│   │   ├── security.py      # JWT & password hashing
│   │   ├── deps.py          # Dependency injection
│   │   └── metrics.py       # Prometheus metrics
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic layer
│   │   ├── analytics.py
│   │   └── alerts.py
│   ├── config.py            # Settings management
│   └── main.py              # Application entry point
├── alembic/                 # Database migrations
├── scripts/
│   └── run_budget_check.py  # Scheduled alert job
├── tests/                   # Test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── Makefile
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Run tests: `make test`
5. Format code: `make format`
6. Commit: `git commit -am 'Add new feature'`
7. Push: `git push origin feature/my-feature`
8. Create a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Built with [FastAPI](https://fastapi.tiangolo.com/), inspired by production API best practices and real-world fintech applications.
