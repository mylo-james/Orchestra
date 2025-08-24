"""TaskEngine interface placeholder (Story 1.3)."""


class TaskEngine:
    """Placeholder for task execution engine."""

    def execute(self, task_id: str, context: dict | None = None) -> dict:
        return {"task_id": task_id, "status": "not_implemented"}

