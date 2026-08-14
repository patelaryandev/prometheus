# Scheduled Budget Alert Job

## Overview

The `scripts/run_budget_check.py` script checks all categories with monthly limits and sends alerts when:
- **80% threshold**: Warning that budget is running low
- **100% threshold**: Alert that budget has been exceeded

## Running Manually

```bash
# With uv (recommended)
uv run python scripts/run_budget_check.py

# Or with python directly
python scripts/run_budget_check.py
```

## Scheduling Options

### Recommended: Render Cron Jobs

**Why Render Cron Jobs are better for this template:**

1. **Unified deployment**: Your app is already configured for Render via `deploy/render.yaml`
2. **Same environment**: Cron jobs run in the same environment as your web service with access to the same DATABASE_URL
3. **Simple configuration**: Add directly to your render.yaml
4. **Cost-effective**: Included in Render's free tier allowance
5. **No additional secrets management**: Cron jobs inherit environment variables from your service

**How to add to render.yaml:**

```yaml
services:
  # ... existing web service ...

  - type: cron
    name: budget-alert-checker
    env: docker
    dockerfilePath: ./Dockerfile
    schedule: "0 9 * * *"  # Daily at 9 AM UTC
    dockerCommand: uv run python scripts/run_budget_check.py
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: fastapi-db
          property: connectionString
      - key: SECRET_KEY
        sync: false  # Will use same SECRET_KEY as web service
```

### Alternative: GitHub Actions Scheduled Workflow

**When to use GitHub Actions:**
- You want the job to run without deploying to Render
- You're testing before deployment
- You want logs in your GitHub repository

**Limitations:**
- Requires setting up DATABASE_URL as a GitHub secret
- Need to expose your database to GitHub Actions runners
- More complex setup for production databases

**Example workflow (.github/workflows/budget-check.yml):**

```yaml
name: Budget Alert Check

on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  budget-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --frozen
      - name: Run budget check
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
        run: uv run python scripts/run_budget_check.py
```

## Recommendation

**Use Render Cron Jobs** because:
1. This template is already configured for Render deployment
2. Simpler setup with no additional secrets to manage
3. Runs in production environment with same database access
4. Better for portfolio/interview demonstration (shows understanding of integrated deployment)

## Email Integration (Future)

Currently, alerts are logged. To integrate real email sending:

1. **Update `app/services/alerts.py`** - Replace `EmailService.send_alert()` stub with:
   - SendGrid API
   - AWS SES
   - Mailgun
   - or similar service

2. **Add environment variables**:
   ```
   EMAIL_SERVICE_API_KEY=your-key
   ALERT_EMAIL_FROM=alerts@yourdomain.com
   ```

3. **Update user model** to store user email preferences
