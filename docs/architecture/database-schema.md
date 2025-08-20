# Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow executions table
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    request TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'analyzing',
    orchestrator_context JSONB DEFAULT '{}',
    temporal_workflow_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result_pr_url VARCHAR(500)
);

-- Agent executions table
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflow_executions(id),
    agent_type VARCHAR(50) NOT NULL,
    input_context JSONB,
    output_result JSONB,
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Knowledge base metadata (vectors stored in Pinecone)
CREATE TABLE knowledge_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pinecone_id VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    usage_count INTEGER DEFAULT 0,
    created_by VARCHAR(50) NOT NULL,
    updated_by VARCHAR(50) NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_workflow_executions_user_id ON workflow_executions(user_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_temporal_id ON workflow_executions(temporal_workflow_id);
CREATE INDEX idx_agent_executions_workflow_id ON agent_executions(workflow_id);
CREATE INDEX idx_knowledge_type ON knowledge_metadata(type);
CREATE INDEX idx_knowledge_confidence ON knowledge_metadata(confidence_score);
CREATE INDEX idx_knowledge_usage ON knowledge_metadata(usage_count);
```
