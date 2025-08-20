# Data Models

## User

**Purpose:** Represents system users who interact with the AI Dev Team Orchestrator

**Key Attributes:**

- id: string (UUID) - Unique user identifier
- email: string - User email for authentication
- name: string - Display name
- preferences: object - User workflow preferences
- created_at: timestamp - Account creation
- last_active: timestamp - Last interaction

### TypeScript Interface

```typescript
interface User {
  id: string;
  email: string;
  name: string;
  preferences: UserPreferences;
  created_at: Date;
  last_active: Date;
}

interface UserPreferences {
  notification_settings: NotificationSettings;
  default_repository?: string;
  workflow_templates: string[];
}
```

### Relationships

- One-to-many with WorkflowExecution
- One-to-many with ProjectKnowledge (via ownership)

## WorkflowExecution

**Purpose:** Tracks individual AI development workflow instances from request to completion

**Key Attributes:**

- id: string (UUID) - Unique workflow identifier
- user_id: string - Requesting user
- request: string - Original natural language request
- status: enum - Current workflow state
- orchestrator_context: object - Current agent context
- temporal_workflow_id: string - Temporal workflow reference
- created_at: timestamp - Workflow start
- completed_at: timestamp? - Workflow completion
- result_pr_url: string? - Final Pull Request URL

### TypeScript Interface

```typescript
interface WorkflowExecution {
  id: string;
  user_id: string;
  request: string;
  status: WorkflowStatus;
  orchestrator_context: OrchestratorContext;
  temporal_workflow_id: string;
  created_at: Date;
  completed_at?: Date;
  result_pr_url?: string;
}

enum WorkflowStatus {
  ANALYZING = 'analyzing',
  PLANNING = 'planning',
  DEVELOPING = 'developing',
  RELEASING = 'releasing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}
```

### Relationships

- Belongs-to User
- One-to-many with AgentExecution
- References ProjectKnowledge entries

## ProjectKnowledge

**Purpose:** Stores evolving project knowledge, patterns, and implementation history for agent learning

**Key Attributes:**

- id: string (UUID) - Unique knowledge entry identifier
- type: enum - Knowledge category (planning, coding, release, architectural)
- title: string - Human-readable knowledge title
- content: string - Structured knowledge content
- embedding: vector - Vector representation for semantic search
- confidence_score: float - Quality/accuracy score (0-1)
- usage_count: integer - How often this knowledge is accessed
- last_updated: timestamp - Most recent update
- created_by: enum - Agent that created this knowledge
- updated_by: enum - Agent that last updated
- version: integer - Knowledge version for conflict resolution

### TypeScript Interface

```typescript
interface ProjectKnowledge {
  id: string;
  type: KnowledgeType;
  title: string;
  content: string;
  embedding: number[]; // 3072 dimensions for text-embedding-3-large
  confidence_score: number;
  usage_count: number;
  last_updated: Date;
  created_by: AgentType;
  updated_by: AgentType;
  version: number;
}

enum KnowledgeType {
  PLANNING = 'planning',
  CODING = 'coding',
  RELEASE = 'release',
  ARCHITECTURAL = 'architectural',
}

enum AgentType {
  ORCHESTRATOR = 'orchestrator',
  DEVELOPER = 'developer',
  RELEASE = 'release',
}
```

### Relationships

- Many-to-many with WorkflowExecution (through usage tracking)
- Self-referential for knowledge evolution chains
