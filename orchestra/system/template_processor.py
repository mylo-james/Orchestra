"""Orchestra template processing engine (Story 1.3)."""

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from jinja2 import (
    Environment,
    Template,
    TemplateError,
    UndefinedError,
    select_autoescape,
)
from jinja2.sandbox import SandboxedEnvironment

from orchestra.system.resource_loader import ResourceMetadata
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TemplateRenderResult:
    """Result of template rendering."""

    success: bool
    template_id: str
    rendered_content: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    render_time: float = 0.0
    variables_used: List[str] = field(default_factory=list)
    variables_missing: List[str] = field(default_factory=list)


class TemplateRenderError(Exception):
    """Exception raised during template rendering."""

    def __init__(
        self,
        message: str,
        template_id: Optional[str] = None,
        line_number: Optional[int] = None,
    ):
        """Initialize template render error."""
        super().__init__(message)
        self.template_id = template_id
        self.line_number = line_number


class TemplateProcessor:
    """Processor for rendering Orchestra templates."""

    def __init__(
        self,
        template_engine: str = "jinja2",
        auto_escape: bool = True,
        sandbox_mode: bool = True,
    ):
        """
        Initialize the template processor.

        Args:
            template_engine: Template engine to use (currently only jinja2)
            auto_escape: Whether to auto-escape HTML/XML content
            sandbox_mode: Whether to use sandboxed environment for security
        """
        self.template_engine = template_engine
        self.auto_escape = auto_escape
        self.sandbox_mode = sandbox_mode

        # Initialize Jinja2 environment
        self.env: Union[Environment, SandboxedEnvironment]
        if sandbox_mode:
            self.env = SandboxedEnvironment(
                autoescape=select_autoescape(["html", "xml"]) if auto_escape else False,
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self.env = Environment(
                autoescape=select_autoescape(["html", "xml"]) if auto_escape else False,
                trim_blocks=True,
                lstrip_blocks=True,
            )

        # Add custom filters
        self._add_custom_filters()

        logger.info(
            f"Initialized TemplateProcessor (engine: {template_engine}, auto_escape: {auto_escape}, sandbox: {sandbox_mode})"
        )

    def render_template(
        self, metadata: ResourceMetadata, content: str, context: Dict[str, Any]
    ) -> TemplateRenderResult:
        """
        Render a template with the given context.

        Args:
            metadata: Template metadata
            content: Template content
            context: Template variables context

        Returns:
            TemplateRenderResult with rendering details
        """
        start_time = time.time()
        template_id = metadata.id

        logger.info(f"Rendering template: {template_id}")

        # Initialize result
        result = TemplateRenderResult(success=False, template_id=template_id)

        try:
            # Pre-process template content
            processed_content = self._preprocess_template(content, metadata)

            # Parse template
            template = self.env.from_string(processed_content)

            # Extract template variables
            variables_used, variables_missing = self._analyze_template_variables(
                template, context
            )
            result.variables_used = variables_used
            result.variables_missing = variables_missing

            # Add warnings for missing variables
            if variables_missing:
                for var in variables_missing:
                    result.warnings.append(f"Missing template variable: {var}")

            # Render template
            rendered_content = template.render(**context)

            # Post-process rendered content
            result.rendered_content = self._postprocess_content(
                rendered_content, metadata
            )
            result.success = True

            logger.info(f"Successfully rendered template: {template_id}")

        except TemplateError as e:
            error_msg = f"Template syntax error: {str(e)}"
            result.errors.append(error_msg)
            logger.error(f"Template rendering failed for {template_id}: {error_msg}")

        except UndefinedError as e:
            error_msg = f"Undefined variable in template: {str(e)}"
            result.errors.append(error_msg)
            logger.error(f"Template rendering failed for {template_id}: {error_msg}")

        except Exception as e:
            error_msg = f"Template rendering error: {str(e)}"
            result.errors.append(error_msg)
            logger.error(f"Template rendering failed for {template_id}: {error_msg}")

        result.render_time = time.time() - start_time

        return result

    def validate_template_syntax(self, content: str) -> List[str]:
        """
        Validate template syntax without rendering.

        Args:
            content: Template content to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            # Try to parse the template
            self.env.from_string(content)

            # Try to get the AST to catch more syntax issues
            self.env.parse(content)

        except TemplateError as e:
            errors.append(f"Template syntax error: {str(e)}")
        except Exception as e:
            errors.append(f"Template validation error: {str(e)}")

        return errors

    def extract_template_variables(self, content: str) -> List[str]:
        """
        Extract all template variables from content.

        Args:
            content: Template content

        Returns:
            List of variable names found in template
        """
        variables = set()

        try:
            # Parse template to get AST
            ast = self.env.parse(content)

            # Extract variables from AST
            variables.update(self._extract_variables_from_ast(ast))

        except Exception as e:
            logger.warning(f"Could not extract variables from template: {e}")

            # Fallback to regex extraction
            var_matches = re.findall(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}", content)
            variables.update(var_matches)

        return sorted(list(variables))

    def _preprocess_template(self, content: str, metadata: ResourceMetadata) -> str:
        """Pre-process template content before rendering."""
        processed = content

        # Remove BMad-specific comments
        processed = re.sub(r"<!-- Powered by BMAD™ Core -->", "", processed)

        # Handle BMad-specific template syntax if needed
        # (Convert any BMad-specific syntax to Jinja2)

        return processed

    def _postprocess_content(self, content: str, metadata: ResourceMetadata) -> str:
        """Post-process rendered content."""
        processed = content

        # Clean up extra whitespace
        processed = re.sub(
            r"\n\s*\n\s*\n", "\n\n", processed
        )  # Multiple blank lines to double
        processed = processed.strip()

        # Add metadata header if it's a document template
        if metadata.resource_type.value == "template" and "document" in metadata.tags:
            header = f"<!-- Generated from template: {metadata.id} -->\n\n"
            processed = header + processed

        return processed

    def _analyze_template_variables(
        self, template: Template, context: Dict[str, Any]
    ) -> tuple[List[str], List[str]]:
        """Analyze template variables usage."""
        try:
            # Get all variables referenced in template
            # Note: template.source is not available, skip AST analysis for now
            referenced_vars: list[str] = []

            # Determine which are provided and which are missing
            provided_vars = set(context.keys())
            referenced_vars_set = set(referenced_vars)

            variables_used = sorted(list(referenced_vars_set & provided_vars))
            variables_missing = sorted(list(referenced_vars_set - provided_vars))

            return variables_used, variables_missing

        except Exception as e:
            logger.warning(f"Could not analyze template variables: {e}")
            return [], []

    def _extract_variables_from_ast(self, ast) -> List[str]:
        """Extract variable names from Jinja2 AST."""
        variables = set()

        def visit_node(node):
            if hasattr(node, "__class__"):
                node_type = node.__class__.__name__

                if node_type == "Name":
                    variables.add(node.name)
                elif node_type == "Getattr":
                    # Handle attribute access like obj.attr
                    if hasattr(node.node, "name"):
                        variables.add(node.node.name)

                # Recursively visit child nodes
                for child in node.iter_child_nodes():
                    visit_node(child)

        try:
            visit_node(ast)
        except Exception as e:
            logger.debug(f"Error extracting variables from AST: {e}")

        return list(variables)

    def _add_custom_filters(self):
        """Add custom Jinja2 filters for Orchestra templates."""

        def markdown_filter(text):
            """Simple markdown-like formatting filter."""
            if not text:
                return ""

            # Convert **bold** to <strong>bold</strong>
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

            # Convert *italic* to <em>italic</em>
            text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)

            # Convert line breaks to <br>
            text = text.replace("\n", "<br>\n")

            return text

        def truncate_words(text, length=50):
            """Truncate text to specified number of words."""
            if not text:
                return ""

            words = text.split()
            if len(words) <= length:
                return text

            return " ".join(words[:length]) + "..."

        def format_list(items, format_type="bullet"):
            """Format a list of items."""
            if not items:
                return ""

            if format_type == "bullet":
                return "\n".join(f"- {item}" for item in items)
            elif format_type == "numbered":
                return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
            else:
                return "\n".join(str(item) for item in items)

        def safe_get(obj, key, default=""):
            """Safely get a value from dict/object with default."""
            try:
                if isinstance(obj, dict):
                    return obj.get(key, default)
                else:
                    return getattr(obj, key, default)
            except Exception:
                return default

        # Register filters
        self.env.filters["markdown"] = markdown_filter
        self.env.filters["truncate_words"] = truncate_words
        self.env.filters["format_list"] = format_list
        self.env.filters["safe_get"] = safe_get

    def get_template_info(self, content: str) -> Dict[str, Any]:
        """
        Get information about a template.

        Args:
            content: Template content

        Returns:
            Dictionary with template information
        """
        info = {
            "variables": self.extract_template_variables(content),
            "syntax_errors": self.validate_template_syntax(content),
            "line_count": len(content.split("\n")),
            "character_count": len(content),
            "has_loops": bool(re.search(r"\{%\s*for\s+", content)),
            "has_conditionals": bool(re.search(r"\{%\s*if\s+", content)),
            "has_includes": bool(re.search(r"\{%\s*include\s+", content)),
            "has_macros": bool(re.search(r"\{%\s*macro\s+", content)),
        }

        return info

    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a simple template string.

        Args:
            template_string: Template string to render
            context: Template variables context

        Returns:
            Rendered string

        Raises:
            TemplateRenderError: If rendering fails
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
        except Exception as e:
            raise TemplateRenderError(f"Failed to render template string: {str(e)}")

    def clear_cache(self):
        """Clear template cache."""
        if hasattr(self.env, "cache") and self.env.cache:
            self.env.cache.clear()
        logger.debug("Template cache cleared")
