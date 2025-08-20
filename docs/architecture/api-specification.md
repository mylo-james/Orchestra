# API Specification

## REST API

```yaml
openapi: 3.0.0
info:
  title: AI Dev Team Orchestrator API
  version: 1.0.0
  description: API for multi-agent AI development workflow orchestration

servers:
  - url: https://api.devteam-orchestrator.com/v1
    description: Production API
  - url: http://localhost:3000/api
    description: Development API

paths:
  /workflows:
    post:
      summary: Start new development workflow
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                request:
                  type: string
                  description: Natural language feature request
                repository_url:
                  type: string
                  description: Target repository URL
                preferences:
                  type: object
                  description: User workflow preferences
      responses:
        201:
          description: Workflow started successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  workflow_id:
                    type: string
                  status:
                    type: string
                  estimated_completion:
                    type: string

  /workflows/{id}:
    get:
      summary: Get workflow status and progress
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Workflow details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WorkflowExecution'

  /knowledge/search:
    post:
      summary: Search project knowledge base
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                query:
                  type: string
                type:
                  type: string
                  enum: [planning, coding, release, architectural]
                limit:
                  type: integer
                  default: 10
      responses:
        200:
          description: Knowledge search results
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ProjectKnowledge'

components:
  schemas:
    WorkflowExecution:
      type: object
      properties:
        id:
          type: string
        user_id:
          type: string
        request:
          type: string
        status:
          type: string
          enum: [analyzing, planning, developing, releasing, completed, failed]
        orchestrator_context:
          type: object
        temporal_workflow_id:
          type: string
        created_at:
          type: string
          format: date-time
        completed_at:
          type: string
          format: date-time
        result_pr_url:
          type: string

    ProjectKnowledge:
      type: object
      properties:
        id:
          type: string
        type:
          type: string
          enum: [planning, coding, release, architectural]
        title:
          type: string
        content:
          type: string
        confidence_score:
          type: number
        usage_count:
          type: integer
        last_updated:
          type: string
          format: date-time
        created_by:
          type: string
          enum: [orchestrator, developer, release]
        version:
          type: integer
```
