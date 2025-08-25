# Epic 1: BMad Foundation & Resource Infrastructure ✅ **COMPLETED**

**Epic Goal:** Build Orchestra's resource-driven persona infrastructure using BMad’s content library as foundation, and enable multi-team/project overlays and context namespacing.

## Stories

- Story 1.1: BMad content inventory and conversion strategy
- Story 1.2: Convert 11 BMad personas to Orchestra YAML personas
- Story 1.3: Integrate tasks, templates, checklists as Orchestra resources
- Story 1.4: Expand CLI persona selection; validate end-to-end execution
- Story 1.5: Persona overlay merge engine (base → team → project precedence)
- Story 1.6: Directory scaffolding for teams/ and projects/ overlays
- Story 1.7: Context-aware loader API (load_persona(pid, team_id, project_id))
- Story 1.8: Namespaced storage (Qdrant collections, PG schemas, logs)
- Story 1.9: CLI commands for team/project init and context switching
- Story 1.10: Tag-based targeting (e.g., role=dev, lang=python, domain=fintech)
- Story 1.11: Broadcast & policy cascade (send update to all matching personas)
- Story 1.12: Policy versioning, diff, rollback for cascaded updates

## Acceptance Criteria (Cross-cutting)

- Resource registry supports versioning/signing/trust levels; provenance attached to outputs
- JSON Schemas for personas/overlays/resources; CI validation with helpful errors
- Cascades support dry-run, preview target set, approval gate, and full audit log
- Structured tracing/logging with team/project/tags/policyVersion; health endpoints for loaders/engines
- Idempotent executions with retries; partial rollback for failed cascades
- Load/perf validated for ≥100 projects, ≥10–20 personas each, ≥10k docs/collection
- Hot-reload is atomic; cache keys include (persona, team, project, version_hash)
