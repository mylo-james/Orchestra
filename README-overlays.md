# Orchestra Persona Overlay System

The Orchestra Persona Overlay System allows you to customize base personas for specific teams and projects without duplicating configuration. This follows a hierarchical precedence model: **base < team < project**.

## Directory Structure

```
orchestra/
├── personas/                    # Base personas (foundation)
│   ├── dev.yaml
│   ├── qa.yaml
│   ├── pm.yaml
│   └── ...
├── teams/                       # Team-specific overlays
│   ├── frontend-team/
│   │   └── personas/
│   │       ├── dev.yaml         # Frontend dev customizations
│   │       └── qa.yaml          # Frontend QA customizations
│   ├── backend-team/
│   │   └── personas/
│   │       └── dev.yaml         # Backend dev customizations
│   └── devops-team/
│       └── personas/
│           └── dev.yaml         # DevOps dev customizations
└── projects/                    # Project-specific overlays
    ├── ecommerce-app/
    │   └── personas/
    │       ├── dev.yaml         # Ecommerce dev requirements
    │       └── qa.yaml          # Ecommerce QA requirements
    ├── fintech-platform/
    │   └── personas/
    │       └── dev.yaml         # Fintech compliance requirements
    └── healthcare-portal/
        └── personas/
            └── dev.yaml         # Healthcare security requirements
```

## Overlay Precedence

When loading a persona, Orchestra merges configurations in this order:

1. **Base Persona** (`orchestra/personas/dev.yaml`) - Foundation
2. **Team Overlay** (`teams/frontend-team/personas/dev.yaml`) - Team practices
3. **Project Overlay** (`projects/ecommerce-app/personas/dev.yaml`) - Project requirements

**Project overlays have the highest precedence** and will override conflicting values from team and base configurations.

## Overlay File Format

Each overlay file follows this YAML structure:

```yaml
# Team or Project Overlay
overlay_type: team  # or "project"
context_id: frontend-team  # team_id or project_id
persona_id: dev
version: 1.0.0
created_by: team-lead
last_modified: 2025-08-24T16:00:00Z

modifications:
  behavioral_contract:
    core_principles:
      - "Team-specific principle 1"
      - "Team-specific principle 2"
    interaction_style: "collaborative"
    halt_conditions:
      - "Team-specific halt condition"
    escalation_triggers:
      - "Team-specific escalation trigger"

  command_interface:
    commands:
      new-team-command:
        description: "Team-specific command"
        execution_pattern: "analyze → execute → validate"
        parameters:
          param1:
            type: "string"
            required: true
        requires_confirmation: false
        timeout_seconds: 120

  resource_dependencies:
    knowledge_sources:
      - "team-style-guide"
    tasks:
      - "team-specific-task"
    tools:
      - "team-tool-1"
      - "team-tool-2"
    templates:
      - "team-template"
    required_services:
      - "team-service"

  identity:
    style: "Team-specific style"
    focus: "Team-specific focus area"
    when_to_use: "When working on team projects"
```

## Merge Behavior

### Lists (Arrays)
Lists are **merged and deduplicated**:
- Base: `["git", "docker"]`
- Team: `["webpack", "cypress"]`
- Project: `["stripe-cli", "redis-cli"]`
- **Result**: `["git", "docker", "webpack", "cypress", "stripe-cli", "redis-cli"]`

### Dictionaries (Objects)
Dictionaries are **merged with project precedence**:
- Commands from all levels are combined
- Conflicting command names: project wins
- Parameters are merged per command

### Scalar Values
Scalar values follow **project precedence**:
- Base: `interaction_style: "collaborative"`
- Team: `interaction_style: "formal"`
- Project: `interaction_style: "security-conscious"`
- **Result**: `"security-conscious"` (project wins)

## Example Scenarios

### Frontend Developer on Ecommerce Project

**Context**: `team_id=frontend-team`, `project_id=ecommerce-app`

**Merged Result**:
- **Base principles**: Clean code, test coverage
- **Team principles**: React best practices, accessibility
- **Project principles**: PCI compliance, performance
- **Tools**: git, docker, webpack, cypress, stripe-cli, redis-cli
- **Commands**: All base + team + project commands
- **Style**: "Security-first, performance-focused" (project wins)

### Backend Developer on Healthcare Project

**Context**: `team_id=backend-team`, `project_id=healthcare-portal`

**Merged Result**:
- **Base principles**: Clean code, test coverage
- **Team principles**: API design, database optimization
- **Project principles**: HIPAA compliance, data encryption
- **Tools**: git, docker, postgresql, redis, encryption-tools
- **Commands**: All base + team + project commands
- **Style**: "HIPAA-compliant, security-first" (project wins)

## Usage with Orchestra CLI

```bash
# Load persona with team context
orchestra agent activate dev --team frontend-team

# Load persona with team and project context
orchestra agent activate dev --team frontend-team --project ecommerce-app

# List available overlays
orchestra overlays list --persona dev

# Validate overlay configuration
orchestra overlays validate teams/frontend-team/personas/dev.yaml

# Show merged result
orchestra overlays preview dev --team frontend-team --project ecommerce-app
```

## Creating New Overlays

### 1. Team Overlay

```bash
# Create team directory
mkdir -p teams/my-team/personas

# Create overlay file
cat > teams/my-team/personas/dev.yaml << EOF
overlay_type: team
context_id: my-team
persona_id: dev
version: 1.0.0

modifications:
  behavioral_contract:
    core_principles:
      - "My team principle"
  resource_dependencies:
    tools:
      - "my-team-tool"
EOF
```

### 2. Project Overlay

```bash
# Create project directory
mkdir -p projects/my-project/personas

# Create overlay file
cat > projects/my-project/personas/dev.yaml << EOF
overlay_type: project
context_id: my-project
persona_id: dev
version: 1.0.0

modifications:
  behavioral_contract:
    core_principles:
      - "My project requirement"
  command_interface:
    commands:
      deploy-my-project:
        description: "Deploy my project"
        execution_pattern: "build → test → deploy"
        requires_confirmation: true
        timeout_seconds: 300
EOF
```

## Validation Rules

1. **Required Fields**: `overlay_type`, `context_id`, `persona_id`, `modifications`
2. **Valid Overlay Types**: `team`, `project`
3. **Context ID**: Must be non-empty string matching team/project name
4. **Persona ID**: Must reference existing base persona
5. **Modifications**: Must be valid YAML dictionary
6. **Schema Compliance**: All modifications must follow PersonaSpec schema

## Performance Considerations

- **Caching**: Merged personas are cached with key `persona:team:project:versions`
- **Hot Reload**: File changes invalidate relevant cache entries
- **Memory Usage**: Cache size limited to 1000 entries with LRU eviction
- **Merge Time**: Target <10ms per merge operation

## Conflict Resolution

When the same field is modified by multiple overlays:

1. **Lists**: Merge all values, remove duplicates
2. **Dictionaries**: Merge keys, project values win for conflicts
3. **Scalars**: Project > Team > Base precedence
4. **Audit Trail**: All conflicts logged with resolution strategy

## Best Practices

### Team Overlays
- Focus on **team practices** and **shared tools**
- Define **coding standards** and **review processes**
- Add **team-specific commands** and **workflows**
- Keep **technology stack** preferences

### Project Overlays
- Focus on **business requirements** and **compliance**
- Define **security policies** and **performance targets**
- Add **project-specific integrations** and **services**
- Override **critical behavioral patterns**

### Naming Conventions
- Team IDs: `frontend-team`, `backend-team`, `data-team`
- Project IDs: `ecommerce-app`, `fintech-platform`, `mobile-app`
- File names: Always match the base persona name (`dev.yaml`, `qa.yaml`)

## Troubleshooting

### Common Issues

1. **Overlay Not Loading**
   - Check file path: `teams/{team-id}/personas/{persona-id}.yaml`
   - Verify YAML syntax with `yamllint`
   - Ensure `context_id` matches directory name

2. **Merge Conflicts**
   - Review audit trail for conflict resolution
   - Use `orchestra overlays preview` to see merged result
   - Check precedence rules (project > team > base)

3. **Performance Issues**
   - Monitor cache hit rates
   - Check for excessive overlay complexity
   - Verify hot-reload is working correctly

### Debugging Commands

```bash
# Validate overlay syntax
orchestra overlays validate teams/frontend-team/personas/dev.yaml

# Show merge conflicts
orchestra overlays conflicts dev --team frontend-team --project ecommerce-app

# Clear cache
orchestra overlays clear-cache

# Show audit trail
orchestra overlays audit --persona dev --limit 10
```

## Migration Guide

### From Single Personas to Overlays

1. **Identify Variations**: Find persona copies with slight differences
2. **Extract Common Base**: Create base persona with shared attributes
3. **Create Team Overlays**: Move team-specific customizations
4. **Create Project Overlays**: Move project-specific requirements
5. **Test Merging**: Verify merged results match original personas
6. **Update CLI Usage**: Add `--team` and `--project` flags

### Example Migration

**Before** (3 separate files):
- `personas/frontend-dev.yaml`
- `personas/backend-dev.yaml`
- `personas/ecommerce-dev.yaml`

**After** (1 base + 2 overlays):
- `personas/dev.yaml` (base)
- `teams/frontend-team/personas/dev.yaml` (team overlay)
- `projects/ecommerce-app/personas/dev.yaml` (project overlay)

This reduces duplication and makes maintenance much easier!
