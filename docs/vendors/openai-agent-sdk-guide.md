# OpenAI Agents SDK Guide

## Overview

The OpenAI Agents SDK is a lightweight framework for building agentic AI applications. It provides simple yet powerful primitives to create complex multi-agent workflows with built-in support for tool calling, agent handoffs, input/output validation, and conversation management.

### Core Concepts

- **Agents**: LLMs equipped with specific instructions and tools
- **Handoffs**: Mechanism for agents to delegate tasks to other specialized agents
- **Guardrails**: Input and output validation for safety and reliability
- **Sessions**: Automatic conversation history management across agent interactions
- **Tools**: Python functions that agents can call, with automatic schema generation
- **Tracing**: Built-in visualization and debugging capabilities

## Installation & Setup

### Python SDK

```bash
pip install openai-agents
```

### JavaScript/TypeScript SDK

```bash
npm install @openai/agents
```

### Environment Setup

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file:

```
OPENAI_API_KEY=your-api-key-here
```

## Basic Usage Examples

### Python - Hello World

```python
from agents import Agent, Runner

# Create a simple agent
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant"
)

# Run the agent
result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)
```

### JavaScript/TypeScript - Hello World

```javascript
import { Agent, run } from '@openai/agents';

const agent = new Agent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant.',
});

const result = await run(
  agent,
  'Write a haiku about recursion in programming.'
);
console.log(result.finalOutput);
```

### Python - Agent with Tools

```python
from agents import Agent, Runner
import requests

def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Mock weather API call
    return f"The weather in {city} is sunny and 72°F"

def search_web(query: str) -> str:
    """Search the web for information."""
    # Mock web search
    return f"Search results for '{query}': [mock results]"

# Create agent with tools
weather_agent = Agent(
    name="WeatherBot",
    instructions="You are a helpful weather assistant. Use the available tools to provide accurate information.",
    functions=[get_weather, search_web]
)

result = Runner.run_sync(
    weather_agent,
    "What's the weather like in San Francisco and find recent news about it?"
)
print(result.final_output)
```

### Advanced Multi-Agent Example with Handoffs

```python
from agents import Agent, Runner

def transfer_to_sales():
    """Transfer the conversation to a sales specialist."""
    return sales_agent

def transfer_to_support():
    """Transfer the conversation to technical support."""
    return support_agent

def transfer_to_billing():
    """Transfer the conversation to billing department."""
    return billing_agent

# Define specialized agents
sales_agent = Agent(
    name="SalesAgent",
    instructions="""You are a sales specialist. Help customers understand our products,
    pricing, and make purchases. Be friendly and persuasive but not pushy."""
)

support_agent = Agent(
    name="SupportAgent",
    instructions="""You are a technical support specialist. Help customers troubleshoot
    issues, provide technical guidance, and resolve problems."""
)

billing_agent = Agent(
    name="BillingAgent",
    instructions="""You are a billing specialist. Help customers with payment issues,
    refunds, subscription changes, and billing questions."""
)

# Main routing agent
router_agent = Agent(
    name="RouterAgent",
    instructions="""You are a customer service router. Listen to customer needs and
    transfer them to the appropriate specialist. You can transfer to sales, support, or billing.""",
    functions=[transfer_to_sales, transfer_to_support, transfer_to_billing]
)

# Example conversation
result = Runner.run_sync(
    router_agent,
    "I'm having trouble with my subscription billing and want to upgrade my plan."
)
print(result.final_output)
```

## Advanced Features

### Guardrails for Input Validation

```python
from agents import Agent, Runner
from pydantic import BaseModel, validator
from typing import List

class UserQuery(BaseModel):
    """Validated user input schema."""
    message: str
    priority: str = "normal"

    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['low', 'normal', 'high', 'urgent']:
            raise ValueError('Priority must be low, normal, high, or urgent')
        return v

    @validator('message')
    def validate_message(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Message must be at least 5 characters long')
        return v

def process_user_request(query: UserQuery) -> str:
    """Process a validated user request."""
    return f"Processing {query.priority} priority request: {query.message}"

agent = Agent(
    name="ValidatedAgent",
    instructions="You process user requests with strict validation.",
    functions=[process_user_request]
)

# This will validate input automatically
result = Runner.run_sync(
    agent,
    "Please process my urgent request about system downtime"
)
```

### Session Management

```python
from agents import Agent, Runner, Session

# Create a persistent session
session = Session()

agent = Agent(
    name="ChatBot",
    instructions="You are a conversational assistant. Remember context from previous messages."
)

# First interaction
result1 = Runner.run_sync(
    agent,
    "My name is Alice and I like programming in Python.",
    session=session
)

# Second interaction - agent remembers context
result2 = Runner.run_sync(
    agent,
    "What programming language did I mention I like?",
    session=session
)

print(result2.final_output)  # Should reference Python and remember Alice
```

### Complex Tool Integration

```python
import json
import sqlite3
from datetime import datetime
from agents import Agent, Runner

def create_database_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(':memory:')
    conn.execute('''
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    return conn

def add_task(title: str, description: str = "") -> str:
    """Add a new task to the database."""
    conn = create_database_connection()
    cursor = conn.execute(
        "INSERT INTO tasks (title, description) VALUES (?, ?)",
        (title, description)
    )
    task_id = cursor.lastrowid
    conn.close()
    return f"Task '{title}' added with ID {task_id}"

def list_tasks(status: str = "all") -> str:
    """List all tasks, optionally filtered by status."""
    conn = create_database_connection()
    if status == "all":
        cursor = conn.execute("SELECT id, title, status FROM tasks")
    else:
        cursor = conn.execute(
            "SELECT id, title, status FROM tasks WHERE status = ?",
            (status,)
        )

    tasks = cursor.fetchall()
    conn.close()

    if not tasks:
        return f"No tasks found with status: {status}"

    task_list = "\n".join([f"{t[0]}: {t[1]} ({t[2]})" for t in tasks])
    return f"Tasks:\n{task_list}"

def update_task_status(task_id: int, status: str) -> str:
    """Update the status of a task."""
    valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
    if status not in valid_statuses:
        return f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

    conn = create_database_connection()
    cursor = conn.execute(
        "UPDATE tasks SET status = ? WHERE id = ?",
        (status, task_id)
    )

    if cursor.rowcount == 0:
        result = f"No task found with ID {task_id}"
    else:
        result = f"Task {task_id} status updated to '{status}'"

    conn.close()
    return result

# Create task management agent
task_agent = Agent(
    name="TaskManager",
    instructions="""You are a task management assistant. You can help users create,
    list, and update tasks. Always confirm actions and provide helpful feedback.""",
    functions=[add_task, list_tasks, update_task_status]
)

# Example usage
result = Runner.run_sync(
    task_agent,
    "Add a task called 'Review code' with description 'Review the new authentication module', then show me all tasks"
)
print(result.final_output)
```

## Integration Patterns

### Async Processing with Background Tasks

```python
import asyncio
from agents import Agent, Runner
from typing import List

async def process_large_dataset(data: List[str]) -> str:
    """Process a large dataset asynchronously."""
    # Simulate time-consuming processing
    await asyncio.sleep(2)
    processed_count = len([item for item in data if len(item) > 5])
    return f"Processed {len(data)} items, {processed_count} met criteria"

async def send_notification(message: str, recipient: str) -> str:
    """Send an async notification."""
    # Simulate API call
    await asyncio.sleep(0.5)
    return f"Notification sent to {recipient}: {message}"

# Create async agent
async_agent = Agent(
    name="AsyncProcessor",
    instructions="You process data and send notifications asynchronously.",
    functions=[process_large_dataset, send_notification]
)

# Use async runner
async def main():
    result = await Runner.run_async(
        async_agent,
        "Process this data: ['item1', 'longer_item2', 'short', 'very_long_item'] and notify admin@example.com when done"
    )
    print(result.final_output)

# Run the async example
asyncio.run(main())
```

### Error Handling and Retries

```python
from agents import Agent, Runner
import random
import time

def unreliable_service(data: str, max_retries: int = 3) -> str:
    """A service that sometimes fails - demonstrates error handling."""
    for attempt in range(max_retries):
        try:
            # Simulate random failures
            if random.random() < 0.6:  # 60% failure rate
                raise ConnectionError(f"Service unavailable (attempt {attempt + 1})")

            # Simulate processing time
            time.sleep(0.5)
            return f"Successfully processed: {data}"

        except ConnectionError as e:
            if attempt == max_retries - 1:
                return f"Failed after {max_retries} attempts: {str(e)}"
            time.sleep(1)  # Wait before retry

    return "Unexpected error"

def robust_api_call(endpoint: str, timeout: int = 30) -> str:
    """Make a robust API call with error handling."""
    try:
        # Simulate API call
        if "invalid" in endpoint.lower():
            raise ValueError("Invalid endpoint provided")

        return f"API call to {endpoint} successful"

    except Exception as e:
        return f"API call failed: {str(e)}"

reliable_agent = Agent(
    name="ReliableAgent",
    instructions="""You make reliable service calls and handle errors gracefully.
    Always retry failed operations and provide clear feedback about what happened.""",
    functions=[unreliable_service, robust_api_call]
)

result = Runner.run_sync(
    reliable_agent,
    "Call the user data service with 'user123' and also call the API endpoint '/users/profile'"
)
print(result.final_output)
```

## Best Practices

### Agent Design

1. **Clear Instructions**: Provide specific, detailed instructions for each agent's role
2. **Single Responsibility**: Keep agents focused on specific domains or tasks
3. **Tool Documentation**: Use clear docstrings for all tools/functions
4. **Error Handling**: Implement proper error handling in tool functions

### Handoff Strategies

```python
# Good: Clear handoff conditions
def should_transfer_to_expert(complexity_level: str) -> bool:
    """Check if task should be handed off to an expert."""
    return complexity_level in ['high', 'expert']

# Good: Contextual handoffs
def transfer_with_context(issue_type: str, context: dict):
    """Transfer to appropriate agent with context."""
    if issue_type == 'billing':
        return billing_agent, f"Customer context: {context}"
    elif issue_type == 'technical':
        return support_agent, f"Technical context: {context}"
    return general_agent, f"General inquiry: {context}"
```

### Security and Validation

```python
from typing import Union
import re

def safe_code_execution(code: str, language: str = "python") -> str:
    """Safely execute code with restrictions."""
    # Validate input
    if language not in ['python', 'javascript']:
        return "Unsupported language"

    # Check for dangerous patterns
    dangerous_patterns = ['import os', 'exec', 'eval', '__import__']
    for pattern in dangerous_patterns:
        if pattern in code:
            return f"Code contains dangerous pattern: {pattern}"

    # Limit code length
    if len(code) > 1000:
        return "Code too long for safe execution"

    return f"Code would execute safely: {code[:100]}..."

def validate_email(email: str) -> Union[str, bool]:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    return "Invalid email format"
```

### Performance Optimization

1. **Batch Operations**: Group related function calls
2. **Async When Possible**: Use async functions for I/O operations
3. **Cache Results**: Cache expensive computations
4. **Limit Context**: Keep conversation history manageable

```python
import functools
from typing import Dict, Any

@functools.lru_cache(maxsize=100)
def expensive_computation(input_data: str) -> str:
    """Cached expensive computation."""
    # Simulate expensive operation
    import time
    time.sleep(1)
    return f"Computed result for: {input_data}"

def batch_process_items(items: list) -> Dict[str, Any]:
    """Process multiple items efficiently."""
    results = {}
    for item in items:
        results[item] = expensive_computation(item)
    return results
```

### Testing Agents

```python
import unittest
from unittest.mock import patch, MagicMock

class TestAgentTools(unittest.TestCase):

    def test_weather_tool(self):
        """Test weather tool returns expected format."""
        result = get_weather("San Francisco")
        self.assertIn("San Francisco", result)
        self.assertIn("°F", result)

    @patch('requests.get')
    def test_api_call_tool(self, mock_get):
        """Test API tool with mocked response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_get.return_value = mock_response

        result = robust_api_call("/test/endpoint")
        self.assertIn("successful", result)

    def test_agent_handoff(self):
        """Test agent handoff logic."""
        result = Runner.run_sync(
            router_agent,
            "I need help with billing"
        )
        # Verify handoff occurred
        self.assertIn("billing", result.final_output.lower())

if __name__ == '__main__':
    unittest.main()
```

## Deployment Considerations

### Production Setup

```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class AgentConfig:
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    max_tokens: int = int(os.getenv("MAX_TOKENS", "2000"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
    timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

# production_agent.py
from agents import Agent, Runner
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_production_agent(config: AgentConfig) -> Agent:
    """Create a production-ready agent with proper configuration."""
    return Agent(
        name="ProductionAgent",
        instructions="You are a production assistant with proper error handling.",
        model=config.model,
        max_tokens=config.max_tokens,
        temperature=config.temperature
    )

def safe_agent_run(agent: Agent, message: str, config: AgentConfig):
    """Run agent with production safety measures."""
    try:
        result = Runner.run_sync(
            agent,
            message,
            timeout=config.timeout
        )
        logger.info(f"Agent completed successfully: {result.final_output[:100]}...")
        return result

    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}")
        return None
```

### Monitoring and Observability

```python
import time
from functools import wraps

def monitor_agent_calls(func):
    """Decorator to monitor agent function calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Function {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {duration:.2f}s: {str(e)}")
            raise
    return wrapper

@monitor_agent_calls
def monitored_tool(data: str) -> str:
    """A tool with built-in monitoring."""
    return f"Processed: {data}"
```

## Resources

### Official Documentation & Repositories

- **Python SDK Documentation**: [openai.github.io/openai-agents-python](https://openai.github.io/openai-agents-python/)
- **JavaScript SDK Documentation**: [openai.github.io/openai-agents-js](https://openai.github.io/openai-agents-js/)
- **Python SDK Repository**: [github.com/openai/openai-agents-python](https://github.com/openai/openai-agents-python)
- **JavaScript SDK Repository**: [github.com/openai/openai-agents-js](https://github.com/openai/openai-agents-js)
- **Official Announcement**: [openai.com/index/new-tools-for-building-agents](https://openai.com/index/new-tools-for-building-agents/)

### Community & Support

- **OpenAI Developer Forum**: [community.openai.com](https://community.openai.com)
- **GitHub Issues**: Report bugs and request features in the respective SDK repositories
- **Examples Repository**: Check SDK repositories for additional examples and patterns

### Related Tools

- **OpenAI Assistants API**: For more complex, stateful agents
- **LangChain**: Alternative framework for building LLM applications
- **Autogen**: Microsoft's multi-agent conversation framework
- **CrewAI**: Another multi-agent framework for complex workflows
