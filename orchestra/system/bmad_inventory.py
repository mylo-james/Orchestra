"""BMad content inventory and conversion strategy for Orchestra integration."""

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field

from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


class BmadContentType(Enum):
    """Types of BMad content that can be inventoried."""
    PERSONA = "persona"
    TASK = "task"
    TEMPLATE = "template"
    CHECKLIST = "checklist"


class BmadContentItem(BaseModel):
    """Represents a single BMad content item with metadata."""
    
    name: str = Field(..., description="Name of the content item")
    path: Path = Field(..., description="Path to the content file")
    content_type: BmadContentType = Field(..., description="Type of content")
    version: str = Field(default="1.0", description="Version of the content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Content metadata")
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "path": str(self.path),
            "content_type": self.content_type.value,
            "version": self.version,
            "metadata": self.metadata
        }


class ResourceSchema(BaseModel):
    """Represents an Orchestra resource schema definition."""
    
    schema_type: str = Field(..., description="Type of resource schema")
    schema_definition: Dict[str, Any] = Field(..., description="Schema definition")
    version: str = Field(default="1.0", description="Schema version")
    
    def is_valid(self) -> bool:
        """Validate the schema definition."""
        required_fields = self._get_required_fields()
        return all(field in self.schema_definition for field in required_fields)
    
    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors."""
        errors = []
        required_fields = self._get_required_fields()
        
        for field in required_fields:
            if field not in self.schema_definition:
                errors.append(f"Missing required field: {field}")
        
        return errors
    
    def _get_required_fields(self) -> List[str]:
        """Get required fields based on schema type."""
        if self.schema_type == "persona":
            return ["identity", "behavioral_contract", "command_interface", "resource_dependencies"]
        elif self.schema_type == "task":
            return ["metadata", "execution", "validation"]
        elif self.schema_type == "template":
            return ["metadata", "variables", "content"]
        elif self.schema_type == "checklist":
            return ["metadata", "items", "validation"]
        return []
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Export as JSON schema for validation."""
        required_fields = self._get_required_fields()
        
        properties = {}
        for field in required_fields:
            properties[field] = {"type": "object"}
        
        return {
            "type": "object",
            "properties": properties,
            "required": required_fields
        }


class ConversionStrategy:
    """Strategy for converting BMad content to Orchestra resource schemas."""
    
    def __init__(self):
        """Initialize conversion strategy."""
        self.validation_rules = self._initialize_validation_rules()
    
    def convert_persona(self, bmad_persona: BmadContentItem) -> ResourceSchema:
        """Convert BMad persona to Orchestra YAML schema."""
        schema_definition = {
            "identity": {
                "name": bmad_persona.metadata.get("name", bmad_persona.name.replace(".md", "")),
                "role": bmad_persona.metadata.get("role", "Agent"),
                "id": bmad_persona.name.replace(".md", "").lower(),
                "title": bmad_persona.metadata.get("title", bmad_persona.metadata.get("role", "Agent")),
                "when_to_use": bmad_persona.metadata.get("when_to_use", "General purpose agent"),
                "style": bmad_persona.metadata.get("style", "Professional and helpful"),
                "focus": bmad_persona.metadata.get("focus", "Task execution")
            },
            "behavioral_contract": {
                "core_principles": bmad_persona.metadata.get("core_principles", []),
                "interaction_style": bmad_persona.metadata.get("interaction_style", "professional"),
                "halt_conditions": bmad_persona.metadata.get("halt_conditions", []),
                "decision_framework": bmad_persona.metadata.get("decision_framework", "analytical")
            },
            "command_interface": {
                "execution_model": "sequential",
                "commands": self._convert_commands(bmad_persona.metadata.get("commands", [])),
                "default_command": "help"
            },
            "resource_dependencies": {
                "knowledge_sources": bmad_persona.metadata.get("knowledge_sources", []),
                "tasks": bmad_persona.metadata.get("tasks", []),
                "templates": bmad_persona.metadata.get("templates", []),
                "tools": bmad_persona.metadata.get("dependencies", []),
                "required_services": bmad_persona.metadata.get("required_services", [])
            },
            "version": bmad_persona.version,
            "enabled": True,
            "experimental": False,
            "deprecated": False
        }
        
        return ResourceSchema(
            schema_type="persona",
            schema_definition=schema_definition,
            version=bmad_persona.version
        )
    
    def convert_task(self, bmad_task: BmadContentItem) -> ResourceSchema:
        """Convert BMad task to Orchestra resource schema."""
        schema_definition = {
            "metadata": {
                "name": bmad_task.name.replace(".md", ""),
                "version": bmad_task.version,
                "description": bmad_task.metadata.get("description", "Task description"),
                "author": bmad_task.metadata.get("author", "BMad"),
                "tags": bmad_task.metadata.get("tags", [])
            },
            "execution": {
                "steps": bmad_task.metadata.get("steps", []),
                "timeout": bmad_task.metadata.get("timeout", 300),
                "retry_policy": bmad_task.metadata.get("retry_policy", {"max_attempts": 3}),
                "dependencies": bmad_task.metadata.get("dependencies", [])
            },
            "validation": {
                "required_inputs": bmad_task.metadata.get("inputs", []),
                "required_outputs": bmad_task.metadata.get("outputs", []),
                "success_criteria": bmad_task.metadata.get("success_criteria", [])
            }
        }
        
        return ResourceSchema(
            schema_type="task",
            schema_definition=schema_definition,
            version=bmad_task.version
        )
    
    def convert_template(self, bmad_template: BmadContentItem) -> ResourceSchema:
        """Convert BMad template to Orchestra resource schema."""
        schema_definition = {
            "metadata": {
                "name": bmad_template.name.replace("-tmpl.yaml", "").replace("-tmpl.md", ""),
                "version": bmad_template.version,
                "description": bmad_template.metadata.get("description", "Template description"),
                "format": bmad_template.metadata.get("format", "markdown"),
                "author": bmad_template.metadata.get("author", "BMad")
            },
            "variables": {
                "required": bmad_template.metadata.get("variables", []),
                "optional": bmad_template.metadata.get("optional_variables", []),
                "defaults": bmad_template.metadata.get("defaults", {})
            },
            "content": {
                "template_path": str(bmad_template.path),
                "sections": bmad_template.metadata.get("sections", []),
                "placeholders": bmad_template.metadata.get("placeholders", [])
            }
        }
        
        return ResourceSchema(
            schema_type="template",
            schema_definition=schema_definition,
            version=bmad_template.version
        )
    
    def convert_checklist(self, bmad_checklist: BmadContentItem) -> ResourceSchema:
        """Convert BMad checklist to Orchestra resource schema."""
        schema_definition = {
            "metadata": {
                "name": bmad_checklist.name.replace("-checklist.md", ""),
                "version": bmad_checklist.version,
                "description": bmad_checklist.metadata.get("description", "Checklist description"),
                "categories": bmad_checklist.metadata.get("categories", []),
                "required": bmad_checklist.metadata.get("required", True)
            },
            "items": {
                "total_count": bmad_checklist.metadata.get("items", 0),
                "categories": bmad_checklist.metadata.get("item_categories", {}),
                "dependencies": bmad_checklist.metadata.get("item_dependencies", {})
            },
            "validation": {
                "completion_threshold": bmad_checklist.metadata.get("completion_threshold", 100),
                "required_items": bmad_checklist.metadata.get("required_items", []),
                "validation_rules": bmad_checklist.metadata.get("validation_rules", [])
            }
        }
        
        return ResourceSchema(
            schema_type="checklist",
            schema_definition=schema_definition,
            version=bmad_checklist.version
        )
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules for converted resources."""
        return self.validation_rules
    
    def plan_directory_structure(self) -> Dict[str, List[str]]:
        """Plan Orchestra resource directory structure."""
        return {
            "orchestra/resources/personas": [
                "Base persona YAML files converted from BMad agents",
                "JSON schema validation files",
                "Documentation and examples"
            ],
            "orchestra/resources/tasks": [
                "Task definition files converted from BMad tasks",
                "Task execution templates",
                "Validation schemas"
            ],
            "orchestra/resources/templates": [
                "Template files converted from BMad templates",
                "Variable definition schemas",
                "Template validation rules"
            ],
            "orchestra/resources/checklists": [
                "Checklist definition files converted from BMad checklists",
                "Checklist item schemas",
                "Completion validation rules"
            ],
            "schemas": [
                "JSON schemas for all resource types",
                "Validation rule definitions",
                "Schema versioning metadata"
            ],
            "validation": [
                "CI validation scripts",
                "Schema validation tools",
                "Error reporting templates"
            ]
        }
    
    def _convert_commands(self, commands: List[str]) -> Dict[str, Dict[str, Any]]:
        """Convert BMad commands to Orchestra command interface format."""
        converted_commands = {}
        
        for command in commands:
            command_name = command.lower().replace(" ", "-")
            converted_commands[command_name] = {
                "description": f"Execute {command} command",
                "execution_pattern": "analyze → execute → validate",
                "parameters": {},
                "timeout_seconds": 120,
                "requires_confirmation": False
            }
        
        return converted_commands
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for resource conversion."""
        return {
            "json_schemas": {
                "persona": "orchestra/schemas/persona.json",
                "task": "orchestra/schemas/task.json",
                "template": "orchestra/schemas/template.json",
                "checklist": "orchestra/schemas/checklist.json"
            },
            "ci_checks": [
                "schema_validation",
                "required_fields_check",
                "version_compatibility_check",
                "dependency_validation"
            ],
            "required_fields": {
                "persona": ["identity", "behavioral_contract", "command_interface"],
                "task": ["metadata", "execution", "validation"],
                "template": ["metadata", "variables", "content"],
                "checklist": ["metadata", "items", "validation"]
            }
        }


class BmadContentInventory:
    """Inventory system for BMad content discovery and categorization."""
    
    def __init__(self, base_path: Path = Path(".bmad-core")):
        """Initialize BMad content inventory."""
        self.base_path = base_path
        self.content_items: List[BmadContentItem] = []
        self.conversion_strategy = ConversionStrategy()
    
    def scan_all(self) -> None:
        """Scan all BMad content directories."""
        logger.info(f"Starting full BMad content scan from {self.base_path}")
        
        self.content_items.clear()
        self.content_items.extend(self.scan_agents())
        self.content_items.extend(self.scan_tasks())
        self.content_items.extend(self.scan_templates())
        self.content_items.extend(self.scan_checklists())
        
        logger.info(f"Completed scan: found {len(self.content_items)} items")
    
    def scan_agents(self) -> List[BmadContentItem]:
        """Scan agents directory for persona definitions."""
        agents_path = self.base_path / "agents"
        return self._scan_directory(agents_path, BmadContentType.PERSONA)
    
    def scan_tasks(self) -> List[BmadContentItem]:
        """Scan tasks directory for task definitions."""
        tasks_path = self.base_path / "tasks"
        return self._scan_directory(tasks_path, BmadContentType.TASK)
    
    def scan_templates(self) -> List[BmadContentItem]:
        """Scan templates directory for template definitions."""
        templates_path = self.base_path / "templates"
        return self._scan_directory(templates_path, BmadContentType.TEMPLATE)
    
    def scan_checklists(self) -> List[BmadContentItem]:
        """Scan checklists directory for checklist definitions."""
        checklists_path = self.base_path / "checklists"
        return self._scan_directory(checklists_path, BmadContentType.CHECKLIST)
    
    def _scan_directory(self, directory: Path, content_type: BmadContentType) -> List[BmadContentItem]:
        """Scan a specific directory for content items."""
        items = []
        
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return items
        
        for file_path in directory.glob("*.md"):
            try:
                metadata = self._extract_metadata(file_path, content_type)
                item = BmadContentItem(
                    name=file_path.name,
                    path=file_path,
                    content_type=content_type,
                    version=metadata.get("version", "1.0"),
                    metadata=metadata
                )
                items.append(item)
                logger.debug(f"Scanned {content_type.value}: {file_path.name}")
            except Exception as e:
                logger.error(f"Error scanning {file_path}: {e}")
        
        # Also scan YAML files for templates
        if content_type == BmadContentType.TEMPLATE:
            for file_path in directory.glob("*.yaml"):
                try:
                    metadata = self._extract_metadata(file_path, content_type)
                    item = BmadContentItem(
                        name=file_path.name,
                        path=file_path,
                        content_type=content_type,
                        version=metadata.get("version", "1.0"),
                        metadata=metadata
                    )
                    items.append(item)
                    logger.debug(f"Scanned {content_type.value}: {file_path.name}")
                except Exception as e:
                    logger.error(f"Error scanning {file_path}: {e}")
        
        return items
    
    def _extract_metadata(self, file_path: Path, content_type: BmadContentType) -> Dict[str, Any]:
        """Extract metadata from a content file."""
        metadata = {}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Extract YAML frontmatter if present
            yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if yaml_match:
                try:
                    yaml_metadata = yaml.safe_load(yaml_match.group(1))
                    if yaml_metadata:
                        metadata.update(yaml_metadata)
                except yaml.YAMLError as e:
                    logger.warning(f"Error parsing YAML frontmatter in {file_path}: {e}")
            
            # Extract content-specific metadata
            if content_type == BmadContentType.PERSONA:
                metadata.update(self._extract_persona_metadata(content))
            elif content_type == BmadContentType.TASK:
                metadata.update(self._extract_task_metadata(content))
            elif content_type == BmadContentType.TEMPLATE:
                metadata.update(self._extract_template_metadata(content, file_path))
            elif content_type == BmadContentType.CHECKLIST:
                metadata.update(self._extract_checklist_metadata(content))
                
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
        
        return metadata
    
    def _extract_persona_metadata(self, content: str) -> Dict[str, Any]:
        """Extract persona-specific metadata."""
        metadata = {}
        
        # Extract role from content
        role_match = re.search(r'role:\s*(.+)', content, re.IGNORECASE)
        if role_match:
            metadata["role"] = role_match.group(1).strip()
        
        # Extract commands from content
        commands = re.findall(r'(?:command|cmd):\s*(.+)', content, re.IGNORECASE)
        if commands:
            metadata["commands"] = [cmd.strip() for cmd in commands]
        
        # Extract dependencies
        deps = re.findall(r'(?:dependency|depends):\s*(.+)', content, re.IGNORECASE)
        if deps:
            metadata["dependencies"] = [dep.strip() for dep in deps]
        
        return metadata
    
    def _extract_task_metadata(self, content: str) -> Dict[str, Any]:
        """Extract task-specific metadata."""
        metadata = {}
        
        # Extract description
        desc_match = re.search(r'description:\s*(.+)', content, re.IGNORECASE)
        if desc_match:
            metadata["description"] = desc_match.group(1).strip()
        
        # Extract inputs and outputs
        inputs = re.findall(r'input:\s*(.+)', content, re.IGNORECASE)
        outputs = re.findall(r'output:\s*(.+)', content, re.IGNORECASE)
        
        if inputs:
            metadata["inputs"] = [inp.strip() for inp in inputs]
        if outputs:
            metadata["outputs"] = [out.strip() for out in outputs]
        
        return metadata
    
    def _extract_template_metadata(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract template-specific metadata."""
        metadata = {}
        
        # Determine format from file extension
        if file_path.suffix == ".yaml":
            metadata["format"] = "yaml"
        elif file_path.suffix == ".md":
            metadata["format"] = "markdown"
        else:
            metadata["format"] = "text"
        
        # Extract variables (placeholders like {{variable}})
        variables = re.findall(r'\{\{(\w+)\}\}', content)
        if variables:
            metadata["variables"] = list(set(variables))
        
        # Extract sections from markdown headers
        if metadata["format"] == "markdown":
            sections = re.findall(r'^#+\s*(.+)', content, re.MULTILINE)
            if sections:
                metadata["sections"] = [section.strip() for section in sections]
        
        return metadata
    
    def _extract_checklist_metadata(self, content: str) -> Dict[str, Any]:
        """Extract checklist-specific metadata."""
        metadata = {}
        
        # Count checklist items
        items = re.findall(r'^\s*[-*]\s*\[[ x]\]', content, re.MULTILINE)
        metadata["items"] = len(items)
        
        # Extract categories from headers
        categories = re.findall(r'^#+\s*(.+)', content, re.MULTILINE)
        if categories:
            metadata["categories"] = [cat.strip() for cat in categories]
        
        return metadata
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive inventory report."""
        report = {
            "personas": [],
            "tasks": [],
            "templates": [],
            "checklists": [],
            "summary": {
                "total_items": len(self.content_items),
                "by_type": {}
            }
        }
        
        # Categorize items
        for item in self.content_items:
            item_dict = item.to_dict()
            
            if item.content_type == BmadContentType.PERSONA:
                report["personas"].append(item_dict)
            elif item.content_type == BmadContentType.TASK:
                report["tasks"].append(item_dict)
            elif item.content_type == BmadContentType.TEMPLATE:
                report["templates"].append(item_dict)
            elif item.content_type == BmadContentType.CHECKLIST:
                report["checklists"].append(item_dict)
        
        # Generate summary
        for content_type in BmadContentType:
            count = len([item for item in self.content_items if item.content_type == content_type])
            report["summary"]["by_type"][content_type.value] = count
        
        return report
    
    def save_report(self, output_path: Path) -> None:
        """Save inventory report to file."""
        report = self.generate_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Inventory report saved to {output_path}")