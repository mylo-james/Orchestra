# Temporal Platform Guide

## Overview

Temporal is a scalable and reliable platform for executing durable functions called **Workflow Executions**. It ensures your application code runs reliably even in the face of failures like network outages or server crashes, allowing you to focus on business logic without writing failure handling code.

### Core Concepts

- **Workflows**: Durable functions that coordinate Activities and handle business logic
- **Activities**: Individual units of work that can fail and be retried
- **Workers**: Processes that execute Workflow and Activity code
- **Temporal Service**: The core platform that manages state and orchestration
- **Temporal Client**: Interface for starting Workflows and sending Signals

## Installation & Setup

### Prerequisites

- Docker (for local development)
- Programming language SDK (Go, Java, Python, TypeScript, .NET, PHP, or Ruby)

### Quick Start with Docker

```bash
# Start Temporal development server
git clone https://github.com/temporalio/docker-compose.git
cd docker-compose
docker-compose up
```

The Temporal Web UI will be available at `http://localhost:8080`.

### SDK Installation

#### Python

```bash
pip install temporalio
```

#### TypeScript/JavaScript

```bash
npm install @temporalio/worker @temporalio/client @temporalio/workflow @temporalio/activity
```

#### Go

```bash
go mod init temporal-example
go get go.temporal.io/sdk
```

## Basic Usage Examples

### Python Example

**Workflow Definition:**

```python
from datetime import timedelta
from temporalio import workflow

@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            compose_greeting,
            name,
            schedule_to_close_timeout=timedelta(seconds=10),
        )

# Activity
from temporalio import activity

@activity.defn
async def compose_greeting(name: str) -> str:
    return f"Hello, {name}!"
```

**Worker:**

```python
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="greeting-task-queue",
        workflows=[GreetingWorkflow],
        activities=[compose_greeting],
    )

    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

**Client:**

```python
import asyncio
from temporalio.client import Client

async def main():
    client = await Client.connect("localhost:7233")

    result = await client.execute_workflow(
        GreetingWorkflow.run,
        "World",
        id="greeting-workflow",
        task_queue="greeting-task-queue",
    )

    print(f"Result: {result}")

asyncio.run(main())
```

### TypeScript Example

**Workflow Definition:**

```typescript
import { proxyActivities } from '@temporalio/workflow';
import * as activities from './activities';

const { composeGreeting } = proxyActivities<typeof activities>({
  scheduleToCloseTimeout: '1 minute',
});

export async function greetingWorkflow(name: string): Promise<string> {
  return await composeGreeting(name);
}
```

**Activities:**

```typescript
export async function composeGreeting(name: string): Promise<string> {
  return `Hello, ${name}!`;
}
```

**Worker:**

```typescript
import { Worker } from '@temporalio/worker';
import * as activities from './activities';

async function run() {
  const worker = await Worker.create({
    workflowsPath: require.resolve('./workflows'),
    activities,
    taskQueue: 'greeting-task-queue',
  });

  await worker.run();
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
```

## Advanced Features

### Signals and Queries

**Signals** allow external systems to send data to running Workflows:

```python
@workflow.defn
class SignalWorkflow:
    def __init__(self) -> None:
        self._updates: list[str] = []

    @workflow.signal
    async def submit_update(self, update: str) -> None:
        self._updates.append(update)

    @workflow.query
    def get_updates(self) -> list[str]:
        return self._updates.copy()

    @workflow.run
    async def run(self) -> str:
        await workflow.wait_condition(lambda: len(self._updates) > 0)
        return f"Received {len(self._updates)} updates"
```

### Timers and Scheduling

```python
@workflow.defn
class TimerWorkflow:
    @workflow.run
    async def run(self) -> str:
        # Sleep for 30 seconds
        await asyncio.sleep(30)

        # Schedule activity for later
        await workflow.execute_activity(
            scheduled_activity,
            schedule_to_start_timeout=timedelta(minutes=5),
        )

        return "Timer workflow completed"
```

### Child Workflows

```python
@workflow.defn
class ParentWorkflow:
    @workflow.run
    async def run(self, data: str) -> str:
        # Start child workflow
        child_result = await workflow.execute_child_workflow(
            ChildWorkflow.run,
            data,
            id="child-workflow",
        )

        return f"Parent got: {child_result}"
```

### Error Handling and Retries

```python
from temporalio.exceptions import ApplicationError

@activity.defn
async def risky_activity(data: str) -> str:
    if random.random() < 0.5:
        raise ApplicationError("Random failure", type="RandomError")
    return f"Processed: {data}"

# In workflow, configure retry policy
await workflow.execute_activity(
    risky_activity,
    data,
    schedule_to_close_timeout=timedelta(minutes=5),
    retry_policy=RetryPolicy(
        initial_interval=timedelta(seconds=1),
        maximum_interval=timedelta(seconds=10),
        maximum_attempts=5,
    ),
)
```

## Best Practices

### Workflow Design

1. **Keep Workflows Deterministic**: Avoid random numbers, current time, or external API calls in Workflow code
2. **Use Activities for Side Effects**: Database calls, API requests, file I/O should be in Activities
3. **Handle Long-Running Operations**: Use heartbeats in Activities that run longer than 10 seconds
4. **Version Your Workflows**: Use `workflow.patch()` for backward compatibility

### Error Handling

1. **Differentiate Error Types**: Use `ApplicationError` for business logic errors, let other exceptions be retried
2. **Configure Appropriate Timeouts**: Set realistic timeouts for Activities and Workflows
3. **Use Retry Policies Wisely**: Configure exponential backoff and maximum attempts

### Performance

1. **Batch Operations**: Group related Activities together
2. **Use Local Activities**: For quick operations that don't need durability guarantees
3. **Monitor Resource Usage**: Use the Temporal Web UI to track Workflow performance

### Testing

```python
import pytest
from temporalio.testing import WorkflowEnvironment

@pytest.mark.asyncio
async def test_greeting_workflow():
    async with WorkflowEnvironment() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[GreetingWorkflow],
            activities=[compose_greeting],
        ):
            result = await env.client.execute_workflow(
                GreetingWorkflow.run,
                "Test",
                id="test-workflow",
                task_queue="test-queue",
            )
            assert result == "Hello, Test!"
```

## Deployment Considerations

### Production Setup

1. **Use External Database**: Configure PostgreSQL or Cassandra instead of SQLite
2. **Scale Workers**: Run multiple Worker instances for high throughput
3. **Monitor Health**: Set up metrics and logging
4. **Secure Communication**: Enable TLS for production environments

### Infrastructure

```yaml
# docker-compose.yml for production-like setup
version: '3.5'
services:
  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - '7233:7233'
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgresql
    depends_on:
      - postgresql

  postgresql:
    image: postgres:13
    environment:
      POSTGRES_PASSWORD: temporal
      POSTGRES_USER: temporal
```

## Common Patterns

### Saga Pattern

```python
@workflow.defn
class SagaWorkflow:
    @workflow.run
    async def run(self, order_data: dict) -> str:
        compensations = []

        try:
            # Step 1: Reserve inventory
            await workflow.execute_activity(reserve_inventory, order_data)
            compensations.append(release_inventory)

            # Step 2: Process payment
            await workflow.execute_activity(process_payment, order_data)
            compensations.append(refund_payment)

            # Step 3: Ship order
            await workflow.execute_activity(ship_order, order_data)

            return "Order completed successfully"

        except Exception:
            # Compensate in reverse order
            for compensation in reversed(compensations):
                await workflow.execute_activity(compensation, order_data)
            raise
```

### Human-in-the-Loop

```python
@workflow.defn
class ApprovalWorkflow:
    def __init__(self) -> None:
        self._approved = False

    @workflow.signal
    async def approve(self) -> None:
        self._approved = True

    @workflow.run
    async def run(self, request: dict) -> str:
        # Send notification for approval
        await workflow.execute_activity(send_approval_request, request)

        # Wait for approval (with timeout)
        try:
            await workflow.wait_condition(
                lambda: self._approved,
                timeout=timedelta(hours=24)
            )
            return "Request approved and processed"
        except asyncio.TimeoutError:
            return "Request timed out"
```

## Resources

- **Official Documentation**: [docs.temporal.io](https://docs.temporal.io/)
- **GitHub Repository**: [github.com/temporalio/temporal](https://github.com/temporalio/temporal)
- **Community Slack**: [temporalio.slack.com](https://temporalio.slack.com)
- **Sample Applications**: [github.com/temporalio/samples](https://github.com/temporalio/samples)
- **SDKs**:
  - Python: [github.com/temporalio/sdk-python](https://github.com/temporalio/sdk-python)
  - TypeScript: [github.com/temporalio/sdk-typescript](https://github.com/temporalio/sdk-typescript)
  - Go: [github.com/temporalio/sdk-go](https://github.com/temporalio/sdk-go)
  - Java: [github.com/temporalio/sdk-java](https://github.com/temporalio/sdk-java)

## CLI Commands

```bash
# Install Temporal CLI
curl -sSf https://temporal.download/cli.sh | sh

# Start a workflow
temporal workflow start \
  --type GreetingWorkflow \
  --task-queue greeting-task-queue \
  --workflow-id my-workflow \
  --input '"World"'

# Query workflow status
temporal workflow describe --workflow-id my-workflow

# Send signal to workflow
temporal workflow signal \
  --workflow-id my-workflow \
  --name submit_update \
  --input '"Hello Signal"'

# List workflows
temporal workflow list

# Show workflow history
temporal workflow show --workflow-id my-workflow
```
