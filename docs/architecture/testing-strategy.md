# Testing Strategy

## Testing Pyramid

```
           E2E Tests (Playwright)
          /                    \
     Integration Tests (pytest + Testing Library)
    /                                           \
Backend Unit (pytest)                    Frontend Unit (Vitest)
```

## Test Organization

### Frontend Tests

```
apps/web/tests/
├── __tests__/                  # Component tests
│   ├── components/
│   ├── hooks/
│   └── pages/
├── e2e/                        # End-to-end tests
│   ├── workflow.spec.ts
│   ├── chat.spec.ts
│   └── auth.spec.ts
└── setup/                      # Test configuration
    ├── jest.config.js
    └── test-utils.tsx
```

### Backend Tests

```
apps/backend/tests/
├── unit/                       # Unit tests
│   ├── agents/
│   ├── services/
│   └── utils/
├── integration/                # Integration tests
│   ├── test_workflows.py
│   ├── test_knowledge.py
│   └── test_github_integration.py
├── fixtures/                   # Test data
└── conftest.py                 # Pytest configuration
```

### E2E Tests

```
tests/e2e/
├── workflow-complete.spec.ts   # Full user journey
├── agent-handoffs.spec.ts      # Multi-agent coordination
├── error-handling.spec.ts      # Failure scenarios
└── knowledge-evolution.spec.ts # Knowledge base updates
```

## Test Examples

### Frontend Component Test

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { workflowService } from '@/services/workflow';

jest.mock('@/services/workflow');

describe('ChatInterface', () => {
  it('should start workflow on message submit', async () => {
    const mockStartWorkflow = jest.fn().mockResolvedValue({
      workflow_id: 'test-id',
      status: 'started',
    });
    (workflowService.startWorkflow as jest.Mock) = mockStartWorkflow;

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(/describe your feature/i);
    const submitButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Add user authentication' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockStartWorkflow).toHaveBeenCalledWith('Add user authentication');
    });
  });
});
```

### Backend API Test

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_start_workflow_endpoint(client: TestClient, mock_auth):
    """Test workflow creation endpoint."""
    request_data = {
        "request": "Add OAuth authentication",
        "repository_url": "https://github.com/test/repo"
    }

    with patch('src.services.orchestrator_service.OrchestratorService.process_user_request') as mock_service:
        mock_service.return_value = {
            "workflow_id": "test-workflow-id",
            "status": "started"
        }

        response = client.post("/api/workflows", json=request_data)

        assert response.status_code == 201
        assert response.json()["workflow_id"] == "test-workflow-id"
        mock_service.assert_called_once()
```

### E2E Test

```typescript
import { test, expect } from '@playwright/test';

test('complete feature implementation workflow', async ({ page }) => {
  // Login
  await page.goto('/');
  await page.click('text=Sign in with GitHub');
  // ... OAuth flow simulation

  // Submit feature request
  await page.fill(
    '[placeholder*="describe your feature"]',
    'Add user profile editing'
  );
  await page.click('button:has-text("Send")');

  // Wait for orchestrator response
  await expect(
    page.locator("text=I'll implement user profile editing")
  ).toBeVisible();

  // Monitor workflow progress
  await expect(page.locator('text=Planning complete')).toBeVisible({
    timeout: 30000,
  });
  await expect(page.locator('text=Code generation in progress')).toBeVisible({
    timeout: 60000,
  });
  await expect(page.locator('text=Pull Request created')).toBeVisible({
    timeout: 120000,
  });

  // Verify PR link
  const prLink = page.locator('a[href*="github.com"][href*="/pull/"]');
  await expect(prLink).toBeVisible();
});
```
