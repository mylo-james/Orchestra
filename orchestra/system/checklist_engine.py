"""Orchestra checklist execution engine (Story 1.3)."""

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from orchestra.system.resource_loader import ResourceMetadata
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


class ChecklistItemStatus(Enum):
    """Status of a checklist item."""

    PENDING = "pending"  # [ ]
    COMPLETED = "completed"  # [x] or [X]
    NOT_APPLICABLE = "not_applicable"  # [N/A]
    FAILED = "failed"  # [!] or custom
    IN_PROGRESS = "in_progress"  # [-]


@dataclass
class ChecklistItem:
    """A single checklist item."""

    id: str
    text: str
    status: ChecklistItemStatus
    section: Optional[str] = None
    auto_check_rule: Optional[str] = None
    validation_rule: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    line_number: int = 0


@dataclass
class ChecklistExecutionResult:
    """Result of checklist execution."""

    success: bool
    checklist_id: str
    total_items: int = 0
    completed_items: int = 0
    not_applicable_items: int = 0
    failed_items: int = 0
    in_progress_items: int = 0
    completion_percentage: float = 0.0
    execution_time: float = 0.0
    items: List[ChecklistItem] = field(default_factory=list)
    validation_results: Optional[Dict[str, Any]] = None
    auto_checked_items: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ChecklistExecutionError(Exception):
    """Exception raised during checklist execution."""

    def __init__(
        self,
        message: str,
        checklist_id: Optional[str] = None,
        item_id: Optional[str] = None,
    ):
        """Initialize checklist execution error."""
        super().__init__(message)
        self.checklist_id = checklist_id
        self.item_id = item_id


class ChecklistEngine:
    """Engine for executing Orchestra checklists."""

    def __init__(
        self, interactive_mode: bool = False, auto_check_enabled: bool = False
    ):
        """
        Initialize the checklist engine.

        Args:
            interactive_mode: Whether to run in interactive mode
            auto_check_enabled: Whether to enable automatic checking based on context
        """
        self.interactive_mode = interactive_mode
        self.auto_check_enabled = auto_check_enabled

        logger.info(
            f"Initialized ChecklistEngine (interactive: {interactive_mode}, auto_check: {auto_check_enabled})"
        )

    def execute_checklist(
        self, metadata: ResourceMetadata, content: str, context: Dict[str, Any]
    ) -> ChecklistExecutionResult:
        """
        Execute a checklist with the given context.

        Args:
            metadata: Checklist metadata
            content: Checklist content (markdown)
            context: Execution context variables

        Returns:
            ChecklistExecutionResult with execution details
        """
        start_time = time.time()
        checklist_id = metadata.id

        logger.info(f"Executing checklist: {checklist_id}")

        # Initialize result
        result = ChecklistExecutionResult(success=False, checklist_id=checklist_id)

        try:
            # Parse checklist items
            items = self._parse_checklist_items(content)
            result.items = items
            result.total_items = len(items)

            if not items:
                result.warnings.append("No checklist items found")
                result.success = True  # Empty checklist is technically successful
                return result

            logger.debug(f"Parsed {len(items)} checklist items for: {checklist_id}")

            # Process items with context
            self._process_checklist_items(items, context, result)

            # Calculate completion statistics
            self._calculate_completion_stats(result)

            # Perform validation if enabled
            if context.get("validate", True):
                result.validation_results = self._validate_checklist_completion(
                    items, context
                )

            result.success = True

            logger.info(
                f"Checklist execution completed: {checklist_id} ({result.completion_percentage:.1f}% complete)"
            )

        except Exception as e:
            error_msg = f"Checklist execution failed: {str(e)}"
            result.errors.append(error_msg)
            logger.error(f"Checklist execution failed for {checklist_id}: {error_msg}")

        result.execution_time = time.time() - start_time

        return result

    def _parse_checklist_items(self, content: str) -> List[ChecklistItem]:
        """Parse checklist items from markdown content."""
        items = []
        current_section = None
        line_number = 0

        lines = content.split("\n")

        for line in lines:
            line_number += 1
            stripped_line = line.strip()

            # Detect section headers
            if stripped_line.startswith("##"):
                current_section = stripped_line.lstrip("# ").strip()
                continue

            # Parse checklist items
            item_match = re.match(r"^\s*-\s*\[([xX \-!N/A]+)\]\s*(.+)$", stripped_line)
            if item_match:
                status_char = item_match.group(1).strip()
                item_text = item_match.group(2).strip()

                # Determine status from checkbox
                if status_char.lower() in ["x"]:
                    status = ChecklistItemStatus.COMPLETED
                elif status_char in ["-"]:
                    status = ChecklistItemStatus.IN_PROGRESS
                elif status_char in ["!"]:
                    status = ChecklistItemStatus.FAILED
                elif status_char.lower() in ["n/a", "na"]:
                    status = ChecklistItemStatus.NOT_APPLICABLE
                else:
                    status = ChecklistItemStatus.PENDING

                # Extract auto-check rule if present
                auto_check_rule = None
                auto_match = re.search(r"\(auto:\s*(.+?)\)", item_text)
                if auto_match:
                    auto_check_rule = auto_match.group(1).strip()
                    item_text = re.sub(r"\s*\(auto:\s*.+?\)", "", item_text).strip()

                # Generate item ID
                item_id = f"item_{len(items) + 1}"

                item = ChecklistItem(
                    id=item_id,
                    text=item_text,
                    status=status,
                    section=current_section,
                    auto_check_rule=auto_check_rule,
                    line_number=line_number,
                )

                items.append(item)

        return items

    def _process_checklist_items(
        self,
        items: List[ChecklistItem],
        context: Dict[str, Any],
        result: ChecklistExecutionResult,
    ):
        """Process checklist items with context."""
        auto_checked_count = 0

        for item in items:
            try:
                # Apply auto-checking if enabled and rule exists
                if (
                    self.auto_check_enabled
                    and item.auto_check_rule
                    and item.status == ChecklistItemStatus.PENDING
                ):
                    if self._evaluate_auto_check_rule(item.auto_check_rule, context):
                        item.status = ChecklistItemStatus.COMPLETED
                        auto_checked_count += 1
                        logger.debug(f"Auto-checked item: {item.text}")

                # Apply validation rules if present
                if item.validation_rule:
                    validation_result = self._evaluate_validation_rule(
                        item.validation_rule, context
                    )
                    if not validation_result:
                        result.warnings.append(
                            f"Validation failed for item: {item.text}"
                        )

            except Exception as e:
                result.warnings.append(f"Error processing item '{item.text}': {str(e)}")
                logger.warning(f"Error processing checklist item: {e}")

        result.auto_checked_items = auto_checked_count

    def _calculate_completion_stats(self, result: ChecklistExecutionResult):
        """Calculate completion statistics."""
        status_counts = {
            ChecklistItemStatus.COMPLETED: 0,
            ChecklistItemStatus.NOT_APPLICABLE: 0,
            ChecklistItemStatus.FAILED: 0,
            ChecklistItemStatus.IN_PROGRESS: 0,
            ChecklistItemStatus.PENDING: 0,
        }

        for item in result.items:
            status_counts[item.status] += 1

        result.completed_items = status_counts[ChecklistItemStatus.COMPLETED]
        result.not_applicable_items = status_counts[ChecklistItemStatus.NOT_APPLICABLE]
        result.failed_items = status_counts[ChecklistItemStatus.FAILED]
        result.in_progress_items = status_counts[ChecklistItemStatus.IN_PROGRESS]

        # Calculate completion percentage (excluding N/A items)
        applicable_items = result.total_items - result.not_applicable_items
        if applicable_items > 0:
            result.completion_percentage = (
                result.completed_items / applicable_items
            ) * 100.0
        else:
            result.completion_percentage = 100.0  # All items are N/A

    def _evaluate_auto_check_rule(self, rule: str, context: Dict[str, Any]) -> bool:
        """Evaluate an auto-check rule against context."""
        try:
            # Simple rule evaluation - can be expanded
            rule = rule.strip()

            # Handle equality checks
            if "==" in rule:
                left, right = rule.split("==", 1)
                left_val = self._get_context_value(left.strip(), context)
                right_val = right.strip().strip("\"'")
                return str(left_val) == right_val

            # Handle greater than checks
            elif ">" in rule:
                left, right = rule.split(">", 1)
                left_val = self._get_context_value(left.strip(), context)
                right_val = float(right.strip())
                return float(left_val) > right_val

            # Handle less than checks
            elif "<" in rule:
                left, right = rule.split("<", 1)
                left_val = self._get_context_value(left.strip(), context)
                right_val = float(right.strip())
                return float(left_val) < right_val

            # Handle boolean checks
            else:
                value = self._get_context_value(rule, context)
                return bool(value)

        except Exception as e:
            logger.warning(f"Failed to evaluate auto-check rule '{rule}': {e}")
            return False

    def _evaluate_validation_rule(self, rule: str, context: Dict[str, Any]) -> bool:
        """Evaluate a validation rule against context."""
        # Similar to auto-check rule evaluation
        return self._evaluate_auto_check_rule(rule, context)

    def _get_context_value(self, key: str, context: Dict[str, Any]) -> Any:
        """Get a value from context, supporting nested keys."""
        try:
            # Handle nested keys like 'obj.attr'
            if "." in key:
                keys = key.split(".")
                value = context
                for k in keys:
                    if isinstance(value, dict):
                        value = value.get(k)
                    else:
                        value = getattr(value, k, None)
                    if value is None:
                        break
                return value
            else:
                return context.get(key)
        except Exception:
            return None

    def _validate_checklist_completion(
        self, items: List[ChecklistItem], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate checklist completion against context."""
        validation_results = {
            "overall_valid": True,
            "required_items_complete": True,
            "validation_errors": [],
            "validation_warnings": [],
        }

        # Check for required items that are not complete
        required_sections = ["Required Items", "Mandatory", "Must Have"]

        for item in items:
            if item.section and any(req in item.section for req in required_sections):
                if item.status not in [
                    ChecklistItemStatus.COMPLETED,
                    ChecklistItemStatus.NOT_APPLICABLE,
                ]:
                    validation_results["required_items_complete"] = False
                    validation_results["validation_errors"].append(
                        f"Required item not complete: {item.text}"
                    )

        # Check context-based validations
        if context.get("test_status") == "failing":
            validation_results["validation_warnings"].append(
                "Tests are failing - review required"
            )

        if context.get("coverage", 0) < 90:
            validation_results["validation_warnings"].append(
                "Code coverage below 90% - review required"
            )

        validation_results["overall_valid"] = (
            validation_results["required_items_complete"]
            and len(validation_results["validation_errors"]) == 0
        )

        return validation_results

    def get_checklist_summary(self, result: ChecklistExecutionResult) -> Dict[str, Any]:
        """Get a summary of checklist execution."""
        return {
            "checklist_id": result.checklist_id,
            "completion_percentage": result.completion_percentage,
            "total_items": result.total_items,
            "completed_items": result.completed_items,
            "pending_items": result.total_items
            - result.completed_items
            - result.not_applicable_items,
            "auto_checked_items": result.auto_checked_items,
            "has_failures": result.failed_items > 0,
            "is_complete": result.completion_percentage >= 100.0,
            "execution_time": result.execution_time,
        }

    def export_checklist_report(
        self, result: ChecklistExecutionResult, format: str = "markdown"
    ) -> str:
        """Export checklist results as a report."""
        if format == "markdown":
            return self._export_markdown_report(result)
        elif format == "json":
            import json

            return json.dumps(self.get_checklist_summary(result), indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_markdown_report(self, result: ChecklistExecutionResult) -> str:
        """Export checklist results as markdown report."""
        lines = [
            f"# Checklist Report: {result.checklist_id}",
            "",
            f"**Completion:** {result.completion_percentage:.1f}%",
            f"**Total Items:** {result.total_items}",
            f"**Completed:** {result.completed_items}",
            f"**Auto-checked:** {result.auto_checked_items}",
            f"**Execution Time:** {result.execution_time:.3f}s",
            "",
        ]

        if result.validation_results:
            lines.extend(
                [
                    "## Validation Results",
                    f"**Overall Valid:** {'✅' if result.validation_results['overall_valid'] else '❌'}",
                    "",
                ]
            )

            if result.validation_results["validation_errors"]:
                lines.append("### Errors")
                for error in result.validation_results["validation_errors"]:
                    lines.append(f"- ❌ {error}")
                lines.append("")

            if result.validation_results["validation_warnings"]:
                lines.append("### Warnings")
                for warning in result.validation_results["validation_warnings"]:
                    lines.append(f"- ⚠️ {warning}")
                lines.append("")

        # Group items by section
        sections = {}
        for item in result.items:
            section = item.section or "General"
            if section not in sections:
                sections[section] = []
            sections[section].append(item)

        lines.append("## Items by Section")
        lines.append("")

        for section, items in sections.items():
            lines.append(f"### {section}")
            lines.append("")

            for item in items:
                status_icon = {
                    ChecklistItemStatus.COMPLETED: "✅",
                    ChecklistItemStatus.PENDING: "⏳",
                    ChecklistItemStatus.NOT_APPLICABLE: "➖",
                    ChecklistItemStatus.FAILED: "❌",
                    ChecklistItemStatus.IN_PROGRESS: "🔄",
                }.get(item.status, "❓")

                lines.append(f"- {status_icon} {item.text}")

            lines.append("")

        return "\n".join(lines)
