# Data and Isolation

- Qdrant
  - One collection per project: orchestra\_{project_id}; record embedding model/version; schedule re‑embed jobs on upgrades.
- PostgreSQL
  - One schema per project for metadata/state; retention/archival policy for inactive projects.
- Logs/Tracing
  - Standard fields: team_id, project_id, tags, policyVersion; health endpoints for loaders/engines.
