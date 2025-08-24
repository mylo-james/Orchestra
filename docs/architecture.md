# Orchestra v2 Architecture (Laptop-Local)

## Technical Summary

- UniversalAgent executes personas that are identity + resource stacks (tasks, templates, checklists, tools).
- Personas are composed via overlays: base → team (optional) → project (optional), deterministic merge.
- Resource system adds ResourceLoader, TaskEngine, TemplateProcessor, ChecklistEngine.
- Per-project isolation: Qdrant collection, PostgreSQL schema, logs/traces tags; optional cross-project weighting.
- Natural-language CLI is primary; structured flags optional. Tag-based broadcast/cascade with dry-run and approvals.

## Component Diagram

```mermaid
graph TB
  CLI[Natural Language CLI] --> Intent[Intent Parser]
  Intent --> Orchestrator[Temporal Orchestrator]
  Orchestrator -->|Activity| Agent[UniversalAgent]
  Agent --> PersonaLoader[PersonaLoader]
  Agent --> ResourceLoader[ResourceLoader]
  ResourceLoader --> TaskEngine[TaskEngine]
  ResourceLoader --> TemplateProcessor[TemplateProcessor]
  ResourceLoader --> ChecklistEngine[ChecklistEngine]
  Agent --> Tools[Tools (GitHub/OpenAI/etc.)]
  Orchestrator --> Qdrant[(Qdrant per-project collections)]
  Orchestrator --> PG[(PostgreSQL per-project schemas)]
  subgraph Namespacing
    Qdrant --- PG
  end
```

## Key Components

- PersonaLoader
  - load_persona(pid, team_id=None, project_id=None): merges base → team → project; atomic hot‑reload; cache key includes (pid, team, project, version_hash).
  - Validates against JSON Schema; emits diff summary on reload.
- ResourceLoader
  - Resolves tasks/templates/checklists from a versioned, signed registry (trust: core/partner/project).
  - Tracks provenance; attaches to outputs.
- TaskEngine / TemplateProcessor / ChecklistEngine
  - Execute workflows, render templates, and enforce checklists; support dry‑run and idempotency keys.
- Natural Language CLI
  - NL → intents (scope: team/project/tags; actor: persona; verb: plan/broadcast/set/rollback).
  - Disambiguation prompts; yolo mode bypasses confirms.

## Data and Isolation

- Qdrant
  - One collection per project: orchestra\_{project_id}; record embedding model/version; schedule re‑embed jobs on upgrades.
- PostgreSQL
  - One schema per project for metadata/state; retention/archival policy for inactive projects.
- Logs/Tracing
  - Standard fields: team_id, project_id, tags, policyVersion; health endpoints for loaders/engines.

## Governance & Safety

- Policy
  - Pin/lock semantics in overlays to avoid unintended cascades; versioned policy packs with diff/rollback.
- Broadcast/Cascade
  - Tag targeting (role=dev, lang=python, domain=fintech); dry‑run preview of targets; approvals; audit logs.
- Execution Safety
  - Secrets scoped per project; sandboxed custom tasks; allow/deny resource lists per team/project.

## Performance & Reliability

- Caching: local caches for resources; LRU for vector queries.
- Concurrency: rate‑limit and shard large cascades.
- Idempotency: keys on executions; retries with backoff; partial rollback on failure.
- Load goals: ≥100 projects, 10–20 personas each, ≥10k docs/collection.

## Source Tree Integration

```
orchestra/
  system/
    loader.py (enhanced overlays)
    resource_loader.py (new)
    task_engine.py (new)
    template_processor.py (new)
    checklist_engine.py (new)
projects/{project_id}/
  config.yaml
  personas/{po|architect|dev|qa}.overlay.yaml
  policies/*.yaml
  kb-seed/*.md
orchestra/personas/base/{po|architect|dev|qa}.yaml
```

## APIs (sketch)

```python
class PersonaLoader:
  def load_persona(self, pid: str, team_id: str|None=None, project_id: str|None=None, force_reload: bool=False) -> PersonaSpec: ...

class ResourceLoader:
  def load_task(self, name: str) -> TaskDef: ...
  def load_template(self, name: str) -> TemplateDef: ...
  def load_checklist(self, name: str) -> ChecklistDef: ...
  def provenance(self, name: str) -> ResourceProvenance: ...

class BroadcastService:
  def preview(self, tags: dict[str,str]) -> list[PersonaContext]: ...
  def cascade_policy(self, persona_id: str, policy_version: str, tags: dict[str,str], dry_run: bool=True) -> CascadeReport: ...
```

## Testing Strategy

- Schema validation tests for personas/overlays/resources.
- End‑to‑end NL CLI flows with disambiguation and yolo.
- Load/perf tests for multi‑project isolation and cascades.
- Safety tests for sandboxing, approvals, and rollback.

## Next Steps

- Implement ResourceLoader/TaskEngine/TemplateProcessor/ChecklistEngine.
- Enhance PersonaLoader with overlay merge + atomic hot‑reload.
- Add NL intents for broadcast/cascade and policy versioning.
- Provision per‑project Qdrant collections and PG schemas with retention.
