"""Persona overlay merge engine for Orchestra.

Provides deterministic merging of base personas with team and project overlays
following the precedence: base < team < project.
"""

import copy
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from orchestra.system.specs import PersonaSpec, PersonaIdentity, BehavioralContract, CommandInterface, ResourceDependencies, CommandDefinition
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


class OverlayType(Enum):
    """Types of persona overlays."""
    TEAM = "team"
    PROJECT = "project"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    PROJECT_WINS = "project_wins"
    TEAM_WINS = "team_wins"
    BASE_WINS = "base_wins"
    MERGE_LISTS = "merge_lists"
    MERGE_DICTS = "merge_dicts"


class OverlayValidationError(Exception):
    """Raised when overlay validation fails."""
    pass


@dataclass
class MergeConflict:
    """Represents a conflict during persona merge."""
    field_path: str
    base_value: Any
    team_value: Optional[Any] = None
    project_value: Optional[Any] = None
    resolution: ConflictResolution = ConflictResolution.PROJECT_WINS
    resolved_value: Any = None


@dataclass
class PersonaOverlay:
    """Represents an overlay modification to a base persona."""
    overlay_type: OverlayType
    context_id: str  # team_id or project_id
    persona_id: str
    modifications: Dict[str, Any]
    version_hash: Optional[str] = None
    created_at: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.version_hash is None:
            self.version_hash = self._generate_version_hash()
    
    def _generate_version_hash(self) -> str:
        """Generate version hash from modifications."""
        content = json.dumps(self.modifications, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:8]
    
    def is_valid(self) -> bool:
        """Validate overlay structure."""
        if not self.context_id or not self.context_id.strip():
            raise OverlayValidationError("context_id cannot be empty")
        
        if not self.persona_id or not self.persona_id.strip():
            raise OverlayValidationError("persona_id cannot be empty")
        
        if not isinstance(self.modifications, dict):
            raise OverlayValidationError("modifications must be a dictionary")
        
        return True


@dataclass
class MergeResult:
    """Result of persona overlay merge operation."""
    success: bool
    merged_persona: Optional[PersonaSpec] = None
    applied_overlays: List[PersonaOverlay] = field(default_factory=list)
    conflicts: List[MergeConflict] = field(default_factory=list)
    merge_time_ms: float = 0.0
    cache_hit: bool = False
    error_message: Optional[str] = None


class OverlayMergeEngine:
    """Engine for merging persona overlays with deterministic conflict resolution."""
    
    def __init__(self, cache_size: int = 1000):
        self.cache: Dict[str, MergeResult] = {}
        self.cache_size = cache_size
        self.audit_trail: List[Dict[str, Any]] = []
        
        # Conflict resolution rules
        self.resolution_rules = {
            # Scalar values: project wins
            "behavioral_contract.interaction_style": ConflictResolution.PROJECT_WINS,
            "behavioral_contract.decision_framework": ConflictResolution.PROJECT_WINS,
            
            # Lists: merge and deduplicate
            "behavioral_contract.core_principles": ConflictResolution.MERGE_LISTS,
            "behavioral_contract.halt_conditions": ConflictResolution.MERGE_LISTS,
            "behavioral_contract.escalation_triggers": ConflictResolution.MERGE_LISTS,
            "resource_dependencies.knowledge_sources": ConflictResolution.MERGE_LISTS,
            "resource_dependencies.tasks": ConflictResolution.MERGE_LISTS,
            "resource_dependencies.tools": ConflictResolution.MERGE_LISTS,
            "resource_dependencies.templates": ConflictResolution.MERGE_LISTS,
            "resource_dependencies.required_services": ConflictResolution.MERGE_LISTS,
            
            # Dictionaries: merge with project precedence
            "command_interface.commands": ConflictResolution.MERGE_DICTS,
            "command_interface.command_aliases": ConflictResolution.MERGE_DICTS,
        }
    
    def merge_persona(
        self,
        base_persona: PersonaSpec,
        team_overlay: Optional[PersonaOverlay] = None,
        project_overlay: Optional[PersonaOverlay] = None
    ) -> MergeResult:
        """Merge base persona with team and project overlays."""
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                base_persona, team_overlay, project_overlay
            )
            
            # Check cache
            if cache_key in self.cache:
                result = copy.deepcopy(self.cache[cache_key])
                result.cache_hit = True
                return result
            
            # Perform merge
            result = self._perform_merge(base_persona, team_overlay, project_overlay)
            
            # Calculate timing
            result.merge_time_ms = (time.time() - start_time) * 1000
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Add to audit trail
            self._add_audit_entry(base_persona, team_overlay, project_overlay, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Merge failed: {e}")
            return MergeResult(
                success=False,
                error_message=str(e),
                merge_time_ms=(time.time() - start_time) * 1000
            )
    
    def _perform_merge(
        self,
        base_persona: PersonaSpec,
        team_overlay: Optional[PersonaOverlay],
        project_overlay: Optional[PersonaOverlay]
    ) -> MergeResult:
        """Perform the actual merge operation."""
        # Start with deep copy of base persona
        merged_persona = copy.deepcopy(base_persona)
        applied_overlays = []
        conflicts = []
        
        # Apply team overlay first
        if team_overlay:
            team_overlay.is_valid()  # Validate
            merged_persona, team_conflicts = self._apply_overlay(
                merged_persona, team_overlay
            )
            applied_overlays.append(team_overlay)
            conflicts.extend(team_conflicts)
        
        # Apply project overlay second (higher precedence)
        if project_overlay:
            project_overlay.is_valid()  # Validate
            merged_persona, project_conflicts = self._apply_overlay(
                merged_persona, project_overlay
            )
            applied_overlays.append(project_overlay)
            conflicts.extend(project_conflicts)
        
        # Detect conflicts between overlays
        if team_overlay and project_overlay:
            overlay_conflicts = self.detect_conflicts(team_overlay, project_overlay)
            conflicts.extend(overlay_conflicts)
        
        return MergeResult(
            success=True,
            merged_persona=merged_persona,
            applied_overlays=applied_overlays,
            conflicts=conflicts
        )
    
    def _apply_overlay(
        self, 
        persona: PersonaSpec, 
        overlay: PersonaOverlay
    ) -> tuple[PersonaSpec, List[MergeConflict]]:
        """Apply a single overlay to a persona."""
        conflicts = []
        
        for section_name, section_data in overlay.modifications.items():
            if hasattr(persona, section_name):
                section_obj = getattr(persona, section_name)
                updated_section, section_conflicts = self._merge_section(
                    section_obj, section_data, section_name, overlay.overlay_type
                )
                setattr(persona, section_name, updated_section)
                conflicts.extend(section_conflicts)
        
        return persona, conflicts
    
    def _merge_section(
        self, 
        base_section: Any, 
        overlay_data: Dict[str, Any], 
        section_name: str,
        overlay_type: OverlayType
    ) -> tuple[Any, List[MergeConflict]]:
        """Merge a specific section (e.g., behavioral_contract, command_interface)."""
        conflicts = []
        
        if section_name == "behavioral_contract":
            return self._merge_behavioral_contract(base_section, overlay_data, overlay_type)
        elif section_name == "command_interface":
            return self._merge_command_interface(base_section, overlay_data, overlay_type)
        elif section_name == "resource_dependencies":
            return self._merge_resource_dependencies(base_section, overlay_data, overlay_type)
        elif section_name == "identity":
            return self._merge_identity(base_section, overlay_data, overlay_type)
        else:
            # Generic merge for unknown sections
            return self._merge_generic(base_section, overlay_data, section_name, overlay_type)
    
    def _merge_behavioral_contract(
        self, 
        base_contract: BehavioralContract, 
        overlay_data: Dict[str, Any],
        overlay_type: OverlayType
    ) -> tuple[BehavioralContract, List[MergeConflict]]:
        """Merge behavioral contract section."""
        conflicts = []
        
        # Handle core_principles (merge lists)
        if "core_principles" in overlay_data:
            base_principles = base_contract.core_principles or []
            overlay_principles = overlay_data["core_principles"]
            merged_principles = list(base_principles) + list(overlay_principles)
            # Remove duplicates while preserving order
            seen = set()
            unique_principles = []
            for principle in merged_principles:
                if principle not in seen:
                    unique_principles.append(principle)
                    seen.add(principle)
            base_contract.core_principles = unique_principles
        
        # Handle scalar fields (project wins)
        scalar_fields = ["interaction_style", "decision_framework"]
        for field in scalar_fields:
            if field in overlay_data:
                old_value = getattr(base_contract, field, None)
                new_value = overlay_data[field]
                if old_value != new_value and old_value is not None:
                    conflict = MergeConflict(
                        field_path=f"behavioral_contract.{field}",
                        base_value=old_value,
                        team_value=new_value if overlay_type == OverlayType.TEAM else None,
                        project_value=new_value if overlay_type == OverlayType.PROJECT else None,
                        resolution=ConflictResolution.PROJECT_WINS,
                        resolved_value=new_value
                    )
                    conflicts.append(conflict)
                setattr(base_contract, field, new_value)
        
        # Handle list fields (merge)
        list_fields = ["halt_conditions", "escalation_triggers"]
        for field in list_fields:
            if field in overlay_data:
                base_list = getattr(base_contract, field, []) or []
                overlay_list = overlay_data[field]
                merged_list = list(base_list) + list(overlay_list)
                # Remove duplicates
                unique_list = list(dict.fromkeys(merged_list))
                setattr(base_contract, field, unique_list)
        
        return base_contract, conflicts
    
    def _merge_command_interface(
        self, 
        base_interface: CommandInterface, 
        overlay_data: Dict[str, Any],
        overlay_type: OverlayType
    ) -> tuple[CommandInterface, List[MergeConflict]]:
        """Merge command interface section."""
        conflicts = []
        
        # Merge commands
        if "commands" in overlay_data:
            base_commands = base_interface.commands or {}
            overlay_commands = overlay_data["commands"]
            
            for cmd_name, cmd_data in overlay_commands.items():
                if cmd_name in base_commands:
                    # Command conflict - project wins
                    conflict = MergeConflict(
                        field_path=f"command_interface.commands.{cmd_name}",
                        base_value=base_commands[cmd_name],
                        team_value=cmd_data if overlay_type == OverlayType.TEAM else None,
                        project_value=cmd_data if overlay_type == OverlayType.PROJECT else None,
                        resolution=ConflictResolution.PROJECT_WINS,
                        resolved_value=cmd_data
                    )
                    conflicts.append(conflict)
                
                # Convert dict to CommandDefinition if needed
                if isinstance(cmd_data, dict):
                    base_commands[cmd_name] = CommandDefinition(
                        description=cmd_data.get("description", ""),
                        execution_pattern=cmd_data.get("execution_pattern", "execute"),
                        parameters=cmd_data.get("parameters", {}),
                        requires_confirmation=cmd_data.get("requires_confirmation", False),
                        timeout_seconds=cmd_data.get("timeout_seconds", 120)
                    )
                else:
                    base_commands[cmd_name] = cmd_data
            
            base_interface.commands = base_commands
        
        # Merge command aliases
        if "command_aliases" in overlay_data:
            base_aliases = base_interface.command_aliases or {}
            overlay_aliases = overlay_data["command_aliases"]
            base_aliases.update(overlay_aliases)
            base_interface.command_aliases = base_aliases
        
        return base_interface, conflicts
    
    def _merge_resource_dependencies(
        self, 
        base_deps: ResourceDependencies, 
        overlay_data: Dict[str, Any],
        overlay_type: OverlayType
    ) -> tuple[ResourceDependencies, List[MergeConflict]]:
        """Merge resource dependencies section."""
        conflicts = []
        
        # List fields to merge
        list_fields = [
            "knowledge_sources", "tasks", "tools", 
            "templates", "required_services"
        ]
        
        for field in list_fields:
            if field in overlay_data:
                base_list = getattr(base_deps, field, []) or []
                overlay_list = overlay_data[field]
                merged_list = list(base_list) + list(overlay_list)
                # Remove duplicates while preserving order
                unique_list = list(dict.fromkeys(merged_list))
                setattr(base_deps, field, unique_list)
        
        return base_deps, conflicts
    
    def _merge_identity(
        self, 
        base_identity: PersonaIdentity, 
        overlay_data: Dict[str, Any],
        overlay_type: OverlayType
    ) -> tuple[PersonaIdentity, List[MergeConflict]]:
        """Merge identity section."""
        conflicts = []
        
        # Identity fields are typically not overridden by overlays
        # But we can allow certain fields like style, focus
        allowed_fields = ["style", "focus", "when_to_use"]
        
        for field in allowed_fields:
            if field in overlay_data:
                old_value = getattr(base_identity, field, None)
                new_value = overlay_data[field]
                if old_value != new_value and old_value is not None:
                    conflict = MergeConflict(
                        field_path=f"identity.{field}",
                        base_value=old_value,
                        team_value=new_value if overlay_type == OverlayType.TEAM else None,
                        project_value=new_value if overlay_type == OverlayType.PROJECT else None,
                        resolution=ConflictResolution.PROJECT_WINS,
                        resolved_value=new_value
                    )
                    conflicts.append(conflict)
                setattr(base_identity, field, new_value)
        
        return base_identity, conflicts
    
    def _merge_generic(
        self, 
        base_obj: Any, 
        overlay_data: Dict[str, Any], 
        section_name: str,
        overlay_type: OverlayType
    ) -> tuple[Any, List[MergeConflict]]:
        """Generic merge for unknown sections."""
        conflicts = []
        
        # For now, just update attributes directly
        for key, value in overlay_data.items():
            if hasattr(base_obj, key):
                old_value = getattr(base_obj, key)
                if old_value != value and old_value is not None:
                    conflict = MergeConflict(
                        field_path=f"{section_name}.{key}",
                        base_value=old_value,
                        team_value=value if overlay_type == OverlayType.TEAM else None,
                        project_value=value if overlay_type == OverlayType.PROJECT else None,
                        resolution=ConflictResolution.PROJECT_WINS,
                        resolved_value=value
                    )
                    conflicts.append(conflict)
                setattr(base_obj, key, value)
        
        return base_obj, conflicts
    
    def detect_conflicts(
        self, 
        team_overlay: PersonaOverlay, 
        project_overlay: PersonaOverlay
    ) -> List[MergeConflict]:
        """Detect conflicts between team and project overlays."""
        conflicts = []
        
        # Find overlapping modification paths
        team_paths = self._get_modification_paths(team_overlay.modifications)
        project_paths = self._get_modification_paths(project_overlay.modifications)
        
        overlapping_paths = team_paths.keys() & project_paths.keys()
        
        for path in overlapping_paths:
            team_value = team_paths[path]
            project_value = project_paths[path]
            
            if team_value != project_value:
                conflict = MergeConflict(
                    field_path=path,
                    base_value=None,  # We don't have base value in this context
                    team_value=team_value,
                    project_value=project_value,
                    resolution=ConflictResolution.PROJECT_WINS,
                    resolved_value=project_value
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _get_modification_paths(
        self, 
        modifications: Dict[str, Any], 
        prefix: str = ""
    ) -> Dict[str, Any]:
        """Get flattened paths from nested modifications."""
        paths = {}
        
        for key, value in modifications.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict) and not self._is_command_definition(value):
                # Recurse into nested dictionaries
                nested_paths = self._get_modification_paths(value, current_path)
                paths.update(nested_paths)
            else:
                # Leaf value
                paths[current_path] = value
        
        return paths
    
    def _is_command_definition(self, value: Dict[str, Any]) -> bool:
        """Check if a dictionary represents a command definition."""
        command_keys = {"description", "execution_pattern", "parameters", "requires_confirmation", "timeout_seconds"}
        return isinstance(value, dict) and any(key in command_keys for key in value.keys())
    
    def generate_cache_key(
        self,
        persona_id: str,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        base_version: str = "latest",
        team_version: str = "latest",
        project_version: str = "latest"
    ) -> str:
        """Generate cache key for persona merge."""
        components = [
            persona_id,
            team_id or "none",
            project_id or "none",
            base_version,
            team_version,
            project_version
        ]
        return ":".join(components)
    
    def _generate_cache_key(
        self,
        base_persona: PersonaSpec,
        team_overlay: Optional[PersonaOverlay],
        project_overlay: Optional[PersonaOverlay]
    ) -> str:
        """Generate cache key from actual objects."""
        return self.generate_cache_key(
            persona_id=base_persona.identity.id,
            team_id=team_overlay.context_id if team_overlay else None,
            project_id=project_overlay.context_id if project_overlay else None,
            base_version="v1",  # TODO: Get actual version
            team_version=team_overlay.version_hash if team_overlay else "none",
            project_version=project_overlay.version_hash if project_overlay else "none"
        )
    
    def _cache_result(self, cache_key: str, result: MergeResult):
        """Cache merge result with LRU eviction."""
        if len(self.cache) >= self.cache_size:
            # Simple FIFO eviction (could be improved to LRU)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[cache_key] = copy.deepcopy(result)
    
    def invalidate_cache(
        self, 
        persona_id: Optional[str] = None,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        """Invalidate cache entries matching the criteria."""
        keys_to_remove = []
        
        for key in self.cache.keys():
            parts = key.split(":")
            if len(parts) >= 3:
                key_persona_id, key_team_id, key_project_id = parts[0], parts[1], parts[2]
                
                should_remove = (
                    (persona_id is None or key_persona_id == persona_id) and
                    (team_id is None or key_team_id == team_id) and
                    (project_id is None or key_project_id == project_id)
                )
                
                if should_remove:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
    
    def _add_audit_entry(
        self,
        base_persona: PersonaSpec,
        team_overlay: Optional[PersonaOverlay],
        project_overlay: Optional[PersonaOverlay],
        result: MergeResult
    ):
        """Add entry to audit trail."""
        entry = {
            "timestamp": time.time(),
            "persona_id": base_persona.identity.id,
            "team_id": team_overlay.context_id if team_overlay else None,
            "project_id": project_overlay.context_id if project_overlay else None,
            "applied_overlays": len(result.applied_overlays),
            "conflicts": len(result.conflicts),
            "merge_time_ms": result.merge_time_ms,
            "cache_hit": result.cache_hit
        }
        
        self.audit_trail.append(entry)
        
        # Keep audit trail size manageable
        if len(self.audit_trail) > 1000:
            self.audit_trail = self.audit_trail[-500:]  # Keep last 500 entries
    
    def validate_overlay_schema(self, overlay_data: Dict[str, Any]) -> bool:
        """Validate overlay schema structure."""
        required_fields = ["overlay_type", "context_id", "persona_id", "modifications"]
        
        for field in required_fields:
            if field not in overlay_data:
                raise OverlayValidationError(f"Missing required field: {field}")
        
        if not overlay_data["context_id"]:
            raise OverlayValidationError("context_id cannot be empty")
        
        if not overlay_data["persona_id"]:
            raise OverlayValidationError("persona_id cannot be empty")
        
        if not isinstance(overlay_data["modifications"], dict):
            raise OverlayValidationError("modifications must be a dictionary")
        
        return True