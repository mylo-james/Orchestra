"""Persona loader for the Universal Agent System."""

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from orchestra.system.specs import (
    BehavioralContract,
    CommandDefinition,
    CommandInterface,
    KnowledgeContext,
    PersonaIdentity,
    PersonaSpec,
    ResourceDependencies,
)
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


class PersonaLoader:
    """
    Loads and manages persona specifications from YAML files.

    This loader implements the override precedence system where personas
    in orchestra/personas/ take precedence over those in .bmad-core/.
    """

    def __init__(self, cache_enabled: bool = True):
        """
        Initialize the persona loader.

        Args:
            cache_enabled: Whether to cache loaded personas
        """
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, PersonaSpec] = {}
        self._persona_paths: Dict[str, Path] = {}

        # Define search paths in precedence order
        self.search_paths = [
            Path("orchestra/personas"),
            Path(".bmad-core/personas"),
        ]

    def discover_personas(self) -> Dict[str, Path]:
        """
        Discover all available persona files.

        Returns:
            Dictionary mapping persona IDs to their file paths
        """
        discovered = {}

        # Search in reverse order so higher precedence paths override
        for search_path in reversed(self.search_paths):
            if not search_path.exists():
                logger.debug(f"Persona search path does not exist: {search_path}")
                continue

            for yaml_file in search_path.glob("*.yaml"):
                persona_id = yaml_file.stem
                discovered[persona_id] = yaml_file
                logger.debug(f"Discovered persona: {persona_id} at {yaml_file}")

        self._persona_paths = discovered
        return discovered

    def load_persona(
        self, persona_id: str, force_reload: bool = False
    ) -> Optional[PersonaSpec]:
        """
        Load a persona specification by ID.

        Args:
            persona_id: ID of the persona to load
            force_reload: Force reload even if cached

        Returns:
            PersonaSpec if found and valid, None otherwise
        """
        # Check cache first
        if self.cache_enabled and not force_reload:
            if persona_id in self._cache:
                logger.debug(f"Returning cached persona: {persona_id}")
                return self._cache[persona_id]

        # Discover personas if not already done
        if not self._persona_paths:
            self.discover_personas()

        # Find persona file
        if persona_id not in self._persona_paths:
            logger.warning(f"Persona not found: {persona_id}")
            return None

        persona_path = self._persona_paths[persona_id]

        try:
            # Load YAML file
            with open(persona_path, "r") as f:
                data = yaml.safe_load(f)

            logger.info(f"Loading persona from: {persona_path}")

            # Parse persona specification
            persona_spec = self._parse_persona_data(data, persona_id)

            # Validate persona
            errors = persona_spec.validate()
            if errors:
                logger.error(f"Persona validation failed for {persona_id}: {errors}")
                return None

            # Cache if enabled
            if self.cache_enabled:
                self._cache[persona_id] = persona_spec

            logger.info(f"Successfully loaded persona: {persona_spec.display_name}")
            return persona_spec

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML for persona {persona_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load persona {persona_id}: {e}", exc_info=True)
            return None

    def _parse_persona_data(self, data: Dict, persona_id: str) -> PersonaSpec:
        """
        Parse raw YAML data into a PersonaSpec.

        Args:
            data: Raw YAML data
            persona_id: ID of the persona being loaded

        Returns:
            Parsed PersonaSpec
        """
        # Parse identity
        identity_data = data.get("identity", {})
        identity = PersonaIdentity(
            name=identity_data.get("name", persona_id),
            id=identity_data.get("id", persona_id),
            title=identity_data.get("title") or "",
            role=identity_data.get("role") or "",
            icon=identity_data.get("icon") or "🤖",
            when_to_use=identity_data.get("when_to_use") or "",
            style=identity_data.get("style") or "",
            focus=identity_data.get("focus") or "",
        )

        # Parse behavioral contract
        behavioral_data = data.get("behavioral_contract", {}) or {}
        behavioral_contract = BehavioralContract(
            core_principles=behavioral_data.get("core_principles", []),
            interaction_style=behavioral_data.get(
                "interaction_style", "conversational"
            ),
            halt_conditions=behavioral_data.get("halt_conditions", []),
            decision_framework=behavioral_data.get("decision_framework"),
            escalation_triggers=behavioral_data.get("escalation_triggers", []),
        )

        # Parse command interface
        command_data = data.get("command_interface", {}) or {}
        commands = {}
        for cmd_name, cmd_info in command_data.get("commands", {}).items():
            if isinstance(cmd_info, dict):
                commands[cmd_name] = CommandDefinition(
                    description=cmd_info.get("description", ""),
                    execution_pattern=cmd_info.get("execution_pattern", ""),
                    parameters=cmd_info.get("parameters", {}),
                    requires_confirmation=cmd_info.get("requires_confirmation", False),
                    timeout_seconds=cmd_info.get("timeout_seconds", 60),
                )

        command_interface = CommandInterface(
            execution_model=command_data.get("execution_model", "sequential"),
            commands=commands,
            default_command=command_data.get("default_command"),
            command_aliases=command_data.get("command_aliases", {}),
        )

        # Parse resource dependencies
        resources_data = data.get("resource_dependencies", {}) or {}
        resource_dependencies = ResourceDependencies(
            knowledge_sources=resources_data.get("knowledge_sources", []),
            tasks=resources_data.get("tasks", []),
            tools=resources_data.get("tools", []),
            templates=resources_data.get("templates", []),
            required_services=resources_data.get("required_services", []),
        )

        # Parse knowledge context if present
        knowledge_context = None
        if "knowledge_context" in data:
            kc_data = data["knowledge_context"]
            knowledge_context = KnowledgeContext(
                domains=kc_data.get("domains", []),
                expertise_areas=kc_data.get("expertise_areas", []),
                learning_sources=kc_data.get("learning_sources", []),
                context_window_size=kc_data.get("context_window_size", 4096),
                memory_retention_policy=kc_data.get(
                    "memory_retention_policy", "session"
                ),
            )

        # Create PersonaSpec
        return PersonaSpec(
            identity=identity,
            behavioral_contract=behavioral_contract,
            command_interface=command_interface,
            resource_dependencies=resource_dependencies,
            knowledge_context=knowledge_context,
            version=data.get("version", "1.0.0"),
            created_by=data.get("created_by", "system"),
            last_modified=data.get("last_modified"),
            tags=data.get("tags", []),
            enabled=data.get("enabled", True),
            experimental=data.get("experimental", False),
            deprecated=data.get("deprecated", False),
        )

    def list_personas(self) -> List[str]:
        """
        List all available persona IDs.

        Returns:
            List of persona IDs
        """
        if not self._persona_paths:
            self.discover_personas()

        return list(self._persona_paths.keys())

    def validate_persona_file(self, file_path: Path) -> List[str]:
        """
        Validate a persona YAML file without loading it into the system.

        Args:
            file_path: Path to the YAML file to validate

        Returns:
            List of validation errors, empty if valid
        """
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)

            persona_id = file_path.stem
            persona_spec = self._parse_persona_data(data, persona_id)

            return persona_spec.validate()

        except yaml.YAMLError as e:
            return [f"YAML parsing error: {e}"]
        except Exception as e:
            return [f"Validation error: {e}"]

    def clear_cache(self) -> None:
        """Clear the persona cache."""
        self._cache.clear()
        logger.info("Persona cache cleared")

    def reload_all(self) -> Dict[str, PersonaSpec]:
        """
        Reload all personas from disk.

        Returns:
            Dictionary of loaded personas
        """
        self.clear_cache()
        self.discover_personas()

        loaded = {}
        for persona_id in self._persona_paths:
            persona = self.load_persona(persona_id, force_reload=True)
            if persona:
                loaded[persona_id] = persona

        logger.info(f"Reloaded {len(loaded)} personas")
        return loaded
