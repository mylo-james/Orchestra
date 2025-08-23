# Orchestra Persona System

## Overview

Orchestra's persona system is the core innovation that distinguishes it from traditional multi-agent frameworks. Instead of hardcoded agent classes, Orchestra uses a single `UniversalAgent` that dynamically embodies different personas defined in YAML configuration files.

## How It Works

### UniversalAgent Architecture

The `UniversalAgent` class (`src/system/agent.py`):
1. **Loads** persona specifications from YAML files
2. **Configures** itself based on the persona's behavioral contract
3. **Executes** commands defined in the persona's command interface
4. **Maintains** security validation and audit logging throughout

### Persona Components

Each persona YAML file defines:

#### 1. Identity
```yaml
identity:
  name: 'Alex'                    # Persona name
  id: 'dev'                      # Unique identifier
  title: 'Orchestra Developer'   # Display title
  role: 'Expert Python developer' # Primary role
  icon: '💻'                     # Visual identifier
  when_to_use: 'Code implementation, debugging...'
  style: 'Concise, pragmatic, security-conscious'
  focus: 'Executing story tasks with precision'
```

#### 2. Behavioral Contract
```yaml
behavioral_contract:
  core_principles:
    - 'CRITICAL: All external API calls must be wrapped in Temporal activities'
    - 'Use async/await patterns for all I/O operations'
    - 'Implement proper error handling with detailed logging'
  interaction_style: 'technical_concise'
  halt_conditions:
    - 'Security validation failures'
    - 'Ambiguous technical requirements'
  decision_framework: 'test_driven_development'
```

#### 3. Command Interface
```yaml
command_interface:
  execution_model: 'sequential'
  commands:
    implement-story:
      description: 'Implement a user story following Orchestra development workflow'
      execution_pattern: 'read_story → analyze_requirements → implement → test → validate'
      parameters:
        story_path: 'Path to the story file'
        test_first: 'Whether to write tests before implementation'
      requires_confirmation: false
      timeout_seconds: 300
```

#### 4. Resource Dependencies
```yaml
resource_dependencies:
  knowledge_sources:
    - 'docs/architecture/coding-standards.md'
    - 'docs/architecture/testing-strategy.md'
  tools:
    - 'github-tools'
    - 'code-analysis-tools'
  required_services:
    - 'openai-sdk'
    - 'temporal-sdk'
```

## Current Personas

### 1. Orchestrator (Brendan)
**File**: `src/personas/orchestrator.yaml`

**Role**: Strategic planner and workflow coordinator
- Analyzes user requests and creates implementation plans
- Coordinates handoffs between specialized personas
- Manages workflow orchestration through Temporal

**Key Commands**:
- `plan` - Analyze request and create detailed implementation plan
- `clarify` - Ask targeted clarifying questions
- `coordinate` - Initiate and coordinate Temporal workflows
- `select-persona` - Choose appropriate specialist for tasks

**When to Use**: Complex requests requiring planning, multi-step workflows, unclear requirements

### 2. Developer (Alex)
**File**: `src/personas/dev.yaml`

**Role**: Expert Python/Temporal developer specializing in implementation
- Handles code generation, testing, and validation
- Follows TDD principles and security best practices
- Implements story tasks with comprehensive test coverage

**Key Commands**:
- `implement-story` - Full story implementation workflow
- `implement-feature` - Specific feature development
- `fix-bug` - Debug and resolve issues
- `create-tests` - Comprehensive test suite creation
- `refactor` - Code quality improvements

**When to Use**: Code implementation, debugging, refactoring, test creation

### 3. Release (Riley)
**File**: `src/personas/release.yaml`

**Role**: Release management and deployment specialist
- Manages Git workflows and branch protection
- Creates pull requests and releases
- Handles deployment coordination

**Key Commands**:
- `create-pr` - Create pull request with documentation
- `create-release` - Version releases with proper tagging
- `merge-pr` - Safe merge with validation
- `deploy` - Environment deployments
- `rollback` - Emergency rollback procedures

**When to Use**: Creating releases, managing branches, deploying code, version control

## Working with Personas

### CLI Usage

```bash
# List available personas
orchestra agent list

# Check persona status
orchestra agent status

# Start specific persona
orchestra agent start orchestrator

# Execute persona command
orchestra agent execute dev implement-story --story-path="story.md"
```

### Persona Switching

The system allows dynamic switching between personas based on task requirements:

1. **Orchestrator** analyzes request and determines best approach
2. **Handoff** to appropriate specialist persona (Dev/Release)
3. **Execution** of specialized commands
4. **Handback** to Orchestrator for coordination

### Command Execution Patterns

Each persona command defines an execution pattern:
- `→` separates sequential steps
- Steps map to actual operations in the UniversalAgent
- Patterns support parallel execution (planned)
- Timeout and confirmation handling built-in

## Security Integration

### Validation
- All persona configurations validated against schema
- Input sanitization for command parameters
- Security scanning of generated outputs

### Audit Logging
- Persona loading and switching events
- Command execution with correlation IDs
- Agent handoff tracking

### Behavioral Constraints
- Halt conditions prevent unsafe operations
- Escalation triggers for critical issues
- Security-first principles enforced

## Extending the System

### Adding New Personas

1. Create new YAML file in `src/personas/`
2. Define identity, behavioral contract, and commands
3. Implement command handlers in UniversalAgent
4. Add persona to CLI registration

### Customizing Existing Personas

1. Modify YAML configuration
2. No code changes required
3. System reloads configuration dynamically

### Command Development

1. Define execution pattern in YAML
2. Implement step handlers in `_execute_step()`
3. Add parameter validation
4. Include security checks

## Best Practices

### Persona Design
- Keep personas focused on specific domains
- Define clear when-to-use guidelines
- Maintain consistent interaction styles
- Include comprehensive halt conditions

### Command Design
- Use descriptive execution patterns
- Include proper timeout values
- Add confirmation for destructive operations
- Implement idempotent operations

### Security Considerations
- Include security principles in behavioral contract
- Implement proper input validation
- Add audit logging for all operations
- Use correlation IDs for traceability

## Future Enhancements

The persona system is designed for extension:
- **Resource System**: Task engines, template processors
- **Learning**: Persona behavior adaptation over time
- **Collaboration**: Multi-persona coordination patterns
- **Composition**: Dynamic persona creation and mixing

This foundation enables Orchestra's evolution while maintaining stability and security.
