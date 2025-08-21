# Hybrid Architecture Migration Guide

## Overview

This guide details the migration from all-cloud architecture to hybrid local/cloud approach for Orchestra project.

## Migration Strategy

### Phase 1: Local Infrastructure Setup

- [ ] Set up gaming laptop as server infrastructure
- [ ] Deploy Temporal Server via Docker
- [ ] Deploy PostgreSQL database for Temporal
- [ ] Deploy Qdrant vector database
- [ ] Update application configuration

### Phase 2: Data Migration

- [ ] Export existing knowledge from Pinecone (if any)
- [ ] Import knowledge data to local Qdrant
- [ ] Verify data integrity and search functionality

### Phase 3: Application Configuration

- [ ] Update environment variables for local endpoints
- [ ] Modify Docker Compose configuration
- [ ] Update connection strings and API endpoints
- [ ] Test local agent workflows

### Phase 4: Testing & Validation

- [ ] Run integration tests with local infrastructure
- [ ] Verify agent handoffs work correctly
- [ ] Test workflow execution and persistence
- [ ] Validate cost savings achieved

## Cost Impact

**Before (Cloud):**

- Temporal Cloud: $100/month
- Pinecone: $70/month
- OpenAI API: $5-25/month
- **Total: ~$175/month**

**After (Hybrid):**

- Local Infrastructure: $0 (using existing gaming laptop)
- Electricity: ~$20/month
- OpenAI API: $5-25/month (unchanged)
- **Total: ~$25/month**

**Annual Savings: ~$1,800**

## Gaming Laptop Requirements

### Minimum Specifications:

- CPU: 4+ cores
- RAM: 16GB (32GB recommended)
- Storage: 500GB+ available
- GPU: Optional but beneficial for future local AI features

### Software Requirements:

- Docker and Docker Compose
- Stable internet connection for OpenAI API
- Port availability: 7233 (Temporal), 6333 (Qdrant), 5432 (PostgreSQL)

## Local Infrastructure Components

### Temporal Server

- **Port:** 7233
- **Web UI:** 8233
- **Database:** PostgreSQL
- **Purpose:** Workflow orchestration and state management

### Qdrant Vector Database

- **Port:** 6333
- **Purpose:** Knowledge storage and semantic search
- **Alternative to:** Pinecone

### PostgreSQL

- **Port:** 5432
- **Purpose:** Temporal server data storage
- **Version:** 15+

## Docker Compose Configuration

Update your `docker-compose.yml` to include:

- Temporal server with PostgreSQL backend
- Qdrant vector database
- PostgreSQL database
- Orchestra application with updated connection strings

## Rollback Plan

If migration issues occur:

1. Switch environment variables back to cloud endpoints
2. Restart application with cloud configuration
3. Verify cloud services are still accessible
4. Debug local infrastructure separately

## Environment Variables

### Local Configuration:

```bash
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233
QDRANT_HOST=localhost
QDRANT_PORT=6333
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### Cloud Fallback:

```bash
TEMPORAL_HOST=your-temporal-cloud-endpoint
PINECONE_API_KEY=your-pinecone-key
```

## Success Criteria

- [ ] All agent workflows execute successfully
- [ ] Cost reduction to ~$25/month achieved
- [ ] Local infrastructure stable and performant
- [ ] Data integrity maintained through migration
- [ ] No functionality regression compared to cloud setup

## Support and Troubleshooting

### Common Issues:

1. **Port conflicts:** Ensure required ports are available
2. **Memory usage:** Monitor RAM usage, consider upgrading if needed
3. **Network connectivity:** Verify local services are accessible
4. **Data migration:** Validate all knowledge data migrated correctly

### Monitoring:

- Set up resource monitoring for gaming laptop
- Monitor application performance
- Track cost savings achievement
- Document any issues for future reference

## Next Steps

After successful migration:

1. Monitor system performance for first week
2. Validate cost savings in first month
3. Consider GPU acceleration for embeddings
4. Plan for local LLM integration in future phases
