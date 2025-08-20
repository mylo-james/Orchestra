# Deployment Architecture

## Deployment Strategy

**Frontend Deployment:**

- **Platform:** Vercel
- **Build Command:** `turbo build --filter=web`
- **Output Directory:** `apps/web/.next`
- **CDN/Edge:** Vercel Edge Network with automatic optimization

**Backend Deployment:**

- **Platform:** AWS Lambda with API Gateway
- **Build Command:** `poetry build && docker build`
- **Deployment Method:** Serverless Framework or CDK
- **Scaling:** Auto-scaling based on request volume

## CI/CD Pipeline

```yaml
name: Deploy AI Dev Team Orchestrator

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          npm ci
          cd apps/backend && poetry install

      - name: Run tests
        run: |
          turbo test
          cd apps/backend && poetry run pytest

  deploy-frontend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}

  deploy-backend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Deploy to AWS Lambda
        run: |
          cd apps/backend
          poetry run serverless deploy --stage production
```

## Environments

| Environment | Frontend URL                               | Backend URL                                    | Purpose                |
| ----------- | ------------------------------------------ | ---------------------------------------------- | ---------------------- |
| Development | <http://localhost:3000>                    | <http://localhost:8000>                        | Local development      |
| Staging     | <https://staging.devteam-orchestrator.com> | <https://api-staging.devteam-orchestrator.com> | Pre-production testing |
| Production  | <https://devteam-orchestrator.com>         | <https://api.devteam-orchestrator.com>         | Live environment       |
