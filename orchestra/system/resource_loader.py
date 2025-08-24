"""Orchestra resource loader for BMad integration (Story 1.3)."""

import hashlib
import re
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


class ResourceType(Enum):
    """Types of resources supported by Orchestra."""

    TASK = "task"
    TEMPLATE = "template"
    CHECKLIST = "checklist"


class ResourceValidationError(Exception):
    """Exception raised when resource validation fails."""

    def __init__(
        self,
        message: str,
        resource_id: Optional[str] = None,
        errors: Optional[List[str]] = None,
    ):
        """Initialize validation error."""
        super().__init__(message)
        self.resource_id = resource_id
        self.errors = errors or []


@dataclass
class ResourceMetadata:
    """Metadata for an Orchestra resource."""

    id: str
    name: str
    resource_type: ResourceType
    version: str = "1.0.0"
    description: str = ""
    author: str = "unknown"
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    trust_level: str = "untrusted"  # untrusted, trusted, verified, signed
    provenance: Optional[str] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class ResourceLoadResult:
    """Result of loading a resource."""

    success: bool
    metadata: Optional[ResourceMetadata]
    content: Optional[str]
    validation_errors: List[str] = field(default_factory=list)
    load_time: float = 0.0
    from_cache: bool = False


@dataclass
class ValidationResult:
    """Result of resource validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ResourceLoader:
    """Loader for Orchestra resources from BMad content."""

    def __init__(
        self,
        base_path: Path = Path(".bmad-core"),
        cache_enabled: bool = True,
        hot_reload_enabled: bool = False,
    ):
        """
        Initialize the resource loader.

        Args:
            base_path: Base path to BMad content directory
            cache_enabled: Whether to enable resource caching
            hot_reload_enabled: Whether to enable hot-reload functionality
        """
        self.base_path = base_path
        self.cache_enabled = cache_enabled
        self.hot_reload_enabled = hot_reload_enabled

        # Resource cache and metadata
        self._cache: Dict[str, ResourceLoadResult] = {}
        self._cache_stats = {"hits": 0, "misses": 0}
        self._file_timestamps: Dict[str, float] = {}
        self._cache_lock = threading.RLock()

        # Resource type mappings
        self._type_directories = {
            ResourceType.TASK: "tasks",
            ResourceType.TEMPLATE: "templates",
            ResourceType.CHECKLIST: "checklists",
        }

        logger.info(f"Initialized ResourceLoader with base_path: {base_path}")

    def discover_resources(self, resource_type: ResourceType) -> List[ResourceMetadata]:
        """
        Discover all resources of a specific type.

        Args:
            resource_type: Type of resources to discover

        Returns:
            List of resource metadata
        """
        logger.info(f"Discovering resources of type: {resource_type.value}")

        directory = self.base_path / self._type_directories[resource_type]

        if not directory.exists():
            logger.warning(f"Resource directory not found: {directory}")
            return []

        resources = []

        for file_path in directory.glob("*.md"):
            try:
                metadata = self._extract_resource_metadata(file_path, resource_type)
                resources.append(metadata)
                logger.debug(f"Discovered resource: {metadata.id}")

            except Exception as e:
                logger.warning(f"Failed to extract metadata from {file_path}: {e}")
                continue

        logger.info(
            f"Discovered {len(resources)} resources of type {resource_type.value}"
        )
        return resources

    def load_resource(
        self, resource_id: str, resource_type: ResourceType
    ) -> ResourceLoadResult:
        """
        Load a specific resource by ID and type.

        Args:
            resource_id: ID of the resource to load
            resource_type: Type of the resource

        Returns:
            ResourceLoadResult with load status and content
        """
        start_time = time.time()

        logger.info(f"Loading resource: {resource_id} (type: {resource_type.value})")

        # Check cache first if enabled
        if self.cache_enabled:
            cached_result = self._get_from_cache(resource_id, resource_type)
            if cached_result:
                self._cache_stats["hits"] += 1
                logger.debug(f"Cache hit for resource: {resource_id}")
                return cached_result

            self._cache_stats["misses"] += 1

        # Load from disk
        try:
            result = self._load_resource_from_disk(resource_id, resource_type)
            result.load_time = time.time() - start_time

            # Cache the result if enabled
            if self.cache_enabled and result.success:
                self._cache_resource(resource_id, resource_type, result)

            logger.info(
                f"Successfully loaded resource: {resource_id} (load_time: {result.load_time:.3f}s)"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to load resource {resource_id}: {e}")
            return ResourceLoadResult(
                success=False,
                metadata=None,
                content=None,
                validation_errors=[str(e)],
                load_time=time.time() - start_time,
            )

    def validate_resource(
        self, metadata: ResourceMetadata, content: str
    ) -> ValidationResult:
        """
        Validate a resource against its schema.

        Args:
            metadata: Resource metadata
            content: Resource content

        Returns:
            ValidationResult with validation status
        """
        logger.debug(f"Validating resource: {metadata.id}")

        errors = []
        warnings = []

        try:
            # Basic metadata validation
            if not metadata.id or not metadata.id.strip():
                errors.append("Resource ID is required and cannot be empty")

            if not metadata.name or not metadata.name.strip():
                errors.append("Resource name is required and cannot be empty")

            if not content or not content.strip():
                errors.append("Resource content is required and cannot be empty")

            # Version format validation
            if not re.match(r"^\d+\.\d+(\.\d+)?$", metadata.version):
                errors.append("Version must be in format X.Y or X.Y.Z")

            # Trust level validation
            valid_trust_levels = ["untrusted", "trusted", "verified", "signed"]
            if metadata.trust_level not in valid_trust_levels:
                errors.append(f"Trust level must be one of: {valid_trust_levels}")

            # Resource type specific validation
            if metadata.resource_type == ResourceType.TASK:
                errors.extend(self._validate_task_content(content))
            elif metadata.resource_type == ResourceType.TEMPLATE:
                errors.extend(self._validate_template_content(content))
            elif metadata.resource_type == ResourceType.CHECKLIST:
                errors.extend(self._validate_checklist_content(content))

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        is_valid = len(errors) == 0

        logger.debug(
            f"Resource validation completed: {metadata.id} (valid: {is_valid})"
        )

        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    def resolve_dependencies(
        self, metadata: ResourceMetadata
    ) -> List[ResourceMetadata]:
        """
        Resolve dependencies for a resource.

        Args:
            metadata: Resource metadata with dependencies

        Returns:
            List of resolved dependency metadata
        """
        logger.debug(f"Resolving dependencies for resource: {metadata.id}")

        resolved_dependencies = []

        for dep_id in metadata.dependencies:
            # Try to find dependency in any resource type
            for resource_type in [
                ResourceType.TASK,
                ResourceType.TEMPLATE,
                ResourceType.CHECKLIST,
            ]:
                result = self.load_resource(dep_id, resource_type)
                if result.success:
                    resolved_dependencies.append(result.metadata)
                    break
            else:
                logger.warning(
                    f"Could not resolve dependency: {dep_id} for resource: {metadata.id}"
                )

        logger.debug(
            f"Resolved {len(resolved_dependencies)}/{len(metadata.dependencies)} dependencies for {metadata.id}"
        )
        return resolved_dependencies

    def _extract_resource_metadata(
        self, file_path: Path, resource_type: ResourceType
    ) -> ResourceMetadata:
        """Extract metadata from a resource file."""
        content = file_path.read_text(encoding="utf-8")

        # Generate resource ID from filename
        resource_id = file_path.stem.lower().replace(" ", "-")

        # Extract title/name from content
        name = resource_id.replace("-", " ").title()
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            name = title_match.group(1).strip()

        # Extract description
        description = ""
        desc_match = re.search(
            r"##\s+Purpose\s*\n\n(.+?)(?=\n##|\n#|$)", content, re.DOTALL
        )
        if not desc_match:
            desc_match = re.search(
                r"##\s+Description\s*\n\n(.+?)(?=\n##|\n#|$)", content, re.DOTALL
            )
        if desc_match:
            description = desc_match.group(1).strip()[:200]  # Limit description length

        # Extract dependencies
        dependencies = []
        dep_matches = re.findall(
            r"(?:depends?|requires?):\s*(.+)", content, re.IGNORECASE
        )
        for match in dep_matches:
            deps = [dep.strip() for dep in match.split(",")]
            dependencies.extend(deps)

        # Extract tags
        tags = [resource_type.value]
        tag_matches = re.findall(r"(?:tags?):\s*(.+)", content, re.IGNORECASE)
        for match in tag_matches:
            new_tags = [tag.strip() for tag in match.split(",")]
            tags.extend(new_tags)

        # Calculate checksum
        checksum = hashlib.md5(content.encode("utf-8")).hexdigest()

        # Get file timestamps
        stat = file_path.stat()
        created_at = time.ctime(stat.st_ctime)
        modified_at = time.ctime(stat.st_mtime)

        # Determine trust level (BMad core content is trusted)
        trust_level = "trusted" if ".bmad-core" in str(file_path) else "untrusted"

        return ResourceMetadata(
            id=resource_id,
            name=name,
            resource_type=resource_type,
            version="1.0.0",  # Default version
            description=description,
            author="bmad-core",
            tags=tags,
            dependencies=dependencies,
            trust_level=trust_level,
            provenance=str(file_path),
            created_at=created_at,
            modified_at=modified_at,
            checksum=checksum,
        )

    def _load_resource_from_disk(
        self, resource_id: str, resource_type: ResourceType
    ) -> ResourceLoadResult:
        """Load resource from disk."""
        directory = self.base_path / self._type_directories[resource_type]

        # Try different filename patterns
        possible_files = [
            directory / f"{resource_id}.md",
            directory / f"{resource_id.replace('-', '_')}.md",
            directory / f"{resource_id.replace('_', '-')}.md",
        ]

        file_path = None
        for path in possible_files:
            if path.exists():
                file_path = path
                break

        if not file_path:
            return ResourceLoadResult(
                success=False,
                metadata=None,
                content=None,
                validation_errors=[f"Resource file not found: {resource_id}"],
            )

        # Read content
        content = file_path.read_text(encoding="utf-8")

        # Extract metadata
        metadata = self._extract_resource_metadata(file_path, resource_type)

        # Validate resource
        validation_result = self.validate_resource(metadata, content)

        if not validation_result.is_valid:
            return ResourceLoadResult(
                success=False,
                metadata=metadata,
                content=content,
                validation_errors=validation_result.errors,
            )

        return ResourceLoadResult(
            success=True,
            metadata=metadata,
            content=content,
            validation_errors=[],
            from_cache=False,
        )

    def _get_from_cache(
        self, resource_id: str, resource_type: ResourceType
    ) -> Optional[ResourceLoadResult]:
        """Get resource from cache if available and valid."""
        with self._cache_lock:
            cache_key = self._generate_cache_key(resource_id, resource_type, "1.0.0")

            if cache_key not in self._cache:
                return None

            cached_result = self._cache[cache_key]

            # Check if hot-reload is enabled and file has changed
            if self.hot_reload_enabled and cached_result.metadata:
                file_path = Path(cached_result.metadata.provenance)
                if file_path.exists():
                    current_mtime = file_path.stat().st_mtime
                    cached_mtime = self._file_timestamps.get(str(file_path), 0)

                    if current_mtime > cached_mtime:
                        # File has changed, invalidate cache
                        logger.debug(
                            f"File changed, invalidating cache for: {resource_id}"
                        )
                        del self._cache[cache_key]
                        return None

            # Return cached result with updated from_cache flag
            cached_result.from_cache = True
            return cached_result

    def _cache_resource(
        self, resource_id: str, resource_type: ResourceType, result: ResourceLoadResult
    ):
        """Cache a resource result."""
        with self._cache_lock:
            cache_key = self._generate_cache_key(
                resource_id, resource_type, result.metadata.version
            )
            self._cache[cache_key] = result

            # Store file timestamp for hot-reload
            if result.metadata and result.metadata.provenance:
                file_path = Path(result.metadata.provenance)
                if file_path.exists():
                    self._file_timestamps[str(file_path)] = file_path.stat().st_mtime

    def _generate_cache_key(
        self, resource_id: str, resource_type: ResourceType, version: str
    ) -> str:
        """Generate a cache key for a resource."""
        return f"{resource_type.value}:{resource_id}:{version}"

    def _validate_task_content(self, content: str) -> List[str]:
        """Validate task-specific content."""
        errors = []

        # Check for required sections
        if "# " not in content:
            errors.append("Task must have a title (# header)")

        if "## Purpose" not in content and "## Description" not in content:
            errors.append("Task should have a Purpose or Description section")

        return errors

    def _validate_template_content(self, content: str) -> List[str]:
        """Validate template-specific content."""
        errors = []

        # Check for template variables (both Jinja2 {{var}} and BMad {var} syntax)
        jinja2_vars = re.findall(r"\{\{(.+?)\}\}", content)
        bmad_vars = re.findall(r"\{([^{}]+)\}", content)

        if not jinja2_vars and not bmad_vars:
            errors.append(
                "Template should contain template variables ({variable} or {{variable}})"
            )

        # Only check Jinja2 syntax if it uses Jinja2 syntax
        if jinja2_vars:
            try:
                from jinja2 import Template

                Template(content)
            except Exception as e:
                errors.append(f"Template syntax error: {str(e)}")

        return errors

    def _validate_checklist_content(self, content: str) -> List[str]:
        """Validate checklist-specific content."""
        errors = []

        # Check for checklist items
        checklist_items = re.findall(r"^\s*-\s*\[[ xX]\]", content, re.MULTILINE)
        if not checklist_items:
            errors.append("Checklist must contain checklist items (- [ ] or - [x])")

        return errors

    def clear_cache(self):
        """Clear the resource cache."""
        with self._cache_lock:
            self._cache.clear()
            self._file_timestamps.clear()
            self._cache_stats = {"hits": 0, "misses": 0}

        logger.info("Resource cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._cache_lock:
            return {
                "cache_size": len(self._cache),
                "hits": self._cache_stats["hits"],
                "misses": self._cache_stats["misses"],
                "hit_rate": self._cache_stats["hits"]
                / max(1, self._cache_stats["hits"] + self._cache_stats["misses"]),
            }
