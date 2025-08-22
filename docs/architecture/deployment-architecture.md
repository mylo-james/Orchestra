# Deployment Architecture

## Hybrid Deployment Strategy

Orchestra uses a **hybrid deployment model** combining local infrastructure for cost efficiency with cloud services for AI capabilities.

### Local Infrastructure (Gaming Laptop)

- **Temporal Server:** Workflow orchestration and state management
- **PostgreSQL:** Database backend for Temporal
- **Qdrant:** Vector database for knowledge management
- **Orchestra CLI:** Python application and agent framework

### Cloud Services

- **OpenAI API:** Agent coordination and complex reasoning
- **GitHub API:** Repository operations and PR management

## Infrastructure Components

### Gaming Laptop Server Setup

**Hardware Requirements:**

- CPU: 4+ cores (8+ recommended)
- RAM: 16GB minimum (32GB recommended)
- Storage: 500GB+ available space
- Network: Stable broadband connection

**Software Stack:**

```yaml
Operating System: Ubuntu 22.04 LTS or macOS
Container Runtime: Docker & Docker Compose
Services:
  - Temporal Server (port 7233)
  - Temporal Web UI (port 8233)
  - PostgreSQL (port 5432)
  - Qdrant (port 6333)
  - Orchestra CLI Application
```

### Docker Compose Architecture

```yaml
version: '3.8'

services:
  # Temporal Server
  temporal:
    image: temporalio/auto-setup:1.24.0
    ports:
      - '7233:7233' # gRPC
      - '8233:8233' # Web UI
    environment:
      - DB=postgresql
      - POSTGRES_SEEDS=postgresql
    depends_on:
      - postgresql

  # PostgreSQL for Temporal
  postgresql:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: temporal
      POSTGRES_USER: temporal
      POSTGRES_PASSWORD: temporal
    ports:
      - '5432:5432'
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports:
      - '6333:6333'
    volumes:
      - qdrant_data:/qdrant/storage

  # Orchestra Application
  orchestra:
    build: .
    environment:
      - TEMPORAL_HOST=temporal
      - TEMPORAL_PORT=7233
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - POSTGRES_HOST=postgresql
    depends_on:
      - temporal
      - qdrant
      - postgresql

volumes:
  postgres_data:
  qdrant_data:
```

## Deployment Environments

| Environment             | Infrastructure               | Purpose                             | Configuration                                |
| ----------------------- | ---------------------------- | ----------------------------------- | -------------------------------------------- |
| **Development**         | Gaming Laptop + Docker       | Local development and testing       | All services local, OpenAI API for agents    |
| **Personal Production** | Gaming Laptop + Docker       | Personal usage and light production | Same as development, optimized for stability |
| **Scale-Out**           | Gaming Laptop + Cloud Hybrid | High usage scenarios                | Local primary, cloud backup/overflow         |

## Cost Comparison

### Current Hybrid Approach

```
Monthly Costs:
- Local Infrastructure: $0 (existing hardware)
- Electricity: ~$20/month
- OpenAI API: $5-25/month
- Total: ~$25/month ($300/year)
```

### Previous All-Cloud Approach

```
Monthly Costs:
- Temporal Cloud: $100/month
- Qdrant: $0/month (local deployment)
- OpenAI API: $5-25/month
- Total: ~$175/month ($2,100/year)

Annual Savings: ~$1,800
```

## Scaling Strategy

### Phase 1: Single Gaming Laptop

- **Capacity:** 100-500 workflows/day
- **Cost:** ~$25/month
- **Reliability:** Single point of failure

### Phase 2: Multi-Machine Local

- **Setup:** Primary + backup gaming laptop/mini PC
- **Capacity:** 500-2000 workflows/day
- **Cost:** ~$50/month
- **Reliability:** High availability with failover

### Phase 3: Hybrid Cloud Scaling

- **Setup:** Local primary + cloud overflow
- **Capacity:** Unlimited
- **Cost:** $50-200/month (scales with usage)
- **Reliability:** Best of both worlds

## CI/CD Pipeline

```yaml
name: Deploy Orchestra

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run tests
        run: |
          poetry run pytest tests/
          poetry run bandit -r src/

      - name: Security audit
        run: |
          poetry run pip-audit

  deploy-local:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: self-hosted # Gaming laptop runner
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to local infrastructure
        run: |
          docker-compose down
          docker-compose pull
          docker-compose up -d

      - name: Health check
        run: |
          ./scripts/health-check.sh
```

## Monitoring and Observability

### Local Monitoring Stack

- **System Metrics:** htop, iostat, Docker stats
- **Application Logs:** Structured logging with correlation IDs
- **Temporal UI:** Built-in workflow monitoring
- **Qdrant Console:** Vector database management

### Health Checks

- Temporal server connectivity
- PostgreSQL database health
- Qdrant vector database status
- OpenAI API connectivity
- Disk space and memory usage

## Backup and Recovery

### Data Backup Strategy

- **PostgreSQL:** Daily automated dumps
- **Qdrant:** Vector data snapshots
- **Application Config:** Git-based configuration management
- **Logs:** Rotating log archives

### Recovery Procedures

1. **Service Recovery:** Docker container restart
2. **Data Recovery:** Restore from latest backup
3. **Full System Recovery:** Rebuild from Docker Compose
4. **Cloud Fallback:** Switch to cloud services if needed

## Security Considerations

### Local Network Security

- Services bound to localhost only
- No external port exposure
- VPN access for remote management
- Regular security updates

### Data Protection

- Local data encryption at rest
- Secure API key management
- No sensitive data in logs
- Regular security audits

## Future Scaling Options

### Hardware Upgrades

- Add more RAM (16GB → 32GB → 64GB)
- Faster storage (NVMe SSD upgrades)
- Better CPU (higher core count)
- Dedicated GPU for local AI inference

### Software Optimizations

- Horizontal scaling with multiple instances
- Load balancing across containers
- Caching layers for performance
- Database sharding and replication

### Hybrid Cloud Integration

- Cloud bursting for peak loads
- Geographic distribution
- Disaster recovery in cloud
- Cost optimization strategies
