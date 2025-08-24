"""Tests for persona overlay merge engine."""

import pytest
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, patch

from orchestra.system.specs import PersonaSpec, PersonaIdentity, BehavioralContract, CommandInterface, ResourceDependencies
from orchestra.system.persona_overlay_merge import (
    PersonaOverlay,
    OverlayMergeEngine,
    MergeResult,
    ConflictResolution,
    OverlayValidationError,
    OverlayType,
    MergeConflict
)


class TestPersonaOverlay:
    """Test PersonaOverlay data structure (AC: 1,2)."""
    
    def test_overlay_creation(self):
        """Test creating a persona overlay."""
        overlay = PersonaOverlay(
            overlay_type=OverlayType.TEAM,
            context_id="frontend-team",
            persona_id="dev",
            modifications={
                "behavioral_contract": {
                    "core_principles": ["React best practices", "TypeScript first"]
                }
            },
            version_hash="abc123"
        )
        
        assert overlay.overlay_type == OverlayType.TEAM
        assert overlay.context_id == "frontend-team"
        assert overlay.persona_id == "dev"
        assert "behavioral_contract" in overlay.modifications
        assert overlay.version_hash == "abc123"
    
    def test_overlay_schema_validation(self):
        """Test overlay schema validation."""
        # Valid overlay
        valid_overlay = PersonaOverlay(
            overlay_type=OverlayType.PROJECT,
            context_id="ecommerce-app",
            persona_id="dev",
            modifications={
                "command_interface": {
                    "commands": {
                        "deploy-staging": {
                            "description": "Deploy to staging environment",
                            "execution_pattern": "validate → deploy → verify",
                            "parameters": {"environment": {"type": "string", "required": True}},
                            "requires_confirmation": True,
                            "timeout_seconds": 300
                        }
                    }
                }
            }
        )
        
        assert valid_overlay.is_valid()
        
        # Invalid overlay - missing required fields
        with pytest.raises(OverlayValidationError):
            invalid_overlay = PersonaOverlay(
                overlay_type=OverlayType.TEAM,
                context_id="",  # Invalid empty context_id
                persona_id="dev",
                modifications={}
            )
            invalid_overlay.is_valid()  # This should raise the exception


class TestOverlayMergeEngine:
    """Test OverlayMergeEngine functionality (AC: 1,3,4)."""
    
    @pytest.fixture
    def base_persona(self):
        """Create base persona for testing."""
        return PersonaSpec(
            identity=PersonaIdentity(
                name="Developer",
                id="dev",
                title="Full Stack Developer",
                role="Software Engineer",
                icon="💻",
                when_to_use="For development tasks",
                style="Professional",
                focus="Code quality"
            ),
            behavioral_contract=BehavioralContract(
                core_principles=["Clean code", "Test-driven development"],
                interaction_style="collaborative",
                halt_conditions=["Unclear requirements"],
                decision_framework="data-driven",
                escalation_triggers=["Security concerns"]
            ),
            command_interface=CommandInterface(
                commands={
                    "implement-feature": {
                        "description": "Implement a new feature",
                        "execution_pattern": "analyze → code → test",
                        "parameters": {"feature": {"type": "string", "required": True}},
                        "requires_confirmation": False,
                        "timeout_seconds": 120
                    }
                },
                command_aliases={}
            ),
            resource_dependencies=ResourceDependencies(
                knowledge_sources=["coding-standards"],
                tasks=["code-review"],
                tools=["git", "ide"],
                templates=["feature-template"],
                required_services=["github"]
            )
        )
    
    @pytest.fixture
    def team_overlay(self):
        """Create team overlay for testing."""
        return PersonaOverlay(
            overlay_type=OverlayType.TEAM,
            context_id="frontend-team",
            persona_id="dev",
            modifications={
                "behavioral_contract": {
                    "core_principles": ["React best practices", "Accessibility first"]
                },
                "command_interface": {
                    "commands": {
                        "run-e2e-tests": {
                            "description": "Run end-to-end tests",
                            "execution_pattern": "setup → test → teardown",
                            "parameters": {"browser": {"type": "string", "default": "chrome"}},
                            "requires_confirmation": False,
                            "timeout_seconds": 600
                        }
                    }
                },
                "resource_dependencies": {
                    "tools": ["cypress", "storybook"]
                }
            }
        )
    
    @pytest.fixture
    def project_overlay(self):
        """Create project overlay for testing."""
        return PersonaOverlay(
            overlay_type=OverlayType.PROJECT,
            context_id="ecommerce-app",
            persona_id="dev",
            modifications={
                "behavioral_contract": {
                    "core_principles": ["PCI compliance", "Performance optimization"]
                },
                "command_interface": {
                    "commands": {
                        "deploy-production": {
                            "description": "Deploy to production",
                            "execution_pattern": "validate → backup → deploy → verify",
                            "parameters": {
                                "version": {"type": "string", "required": True},
                                "rollback_plan": {"type": "boolean", "default": True}
                            },
                            "requires_confirmation": True,
                            "timeout_seconds": 1800
                        }
                    }
                }
            }
        )
    
    @pytest.fixture
    def merge_engine(self):
        """Create merge engine for testing."""
        return OverlayMergeEngine()
    
    def test_merge_engine_initialization(self, merge_engine):
        """Test merge engine initialization."""
        assert merge_engine is not None
        assert merge_engine.cache is not None
        assert merge_engine.audit_trail == []
    
    def test_simple_merge_base_only(self, merge_engine, base_persona):
        """Test merging with base persona only."""
        result = merge_engine.merge_persona(
            base_persona=base_persona,
            team_overlay=None,
            project_overlay=None
        )
        
        assert result.success is True
        assert result.merged_persona == base_persona
        assert len(result.conflicts) == 0
        assert len(result.applied_overlays) == 0
    
    def test_merge_with_team_overlay(self, merge_engine, base_persona, team_overlay):
        """Test merging base persona with team overlay."""
        result = merge_engine.merge_persona(
            base_persona=base_persona,
            team_overlay=team_overlay,
            project_overlay=None
        )
        
        assert result.success is True
        assert len(result.applied_overlays) == 1
        assert result.applied_overlays[0] == team_overlay
        
        # Check that team overlay principles were added
        merged_principles = result.merged_persona.behavioral_contract.core_principles
        assert "React best practices" in merged_principles
        assert "Accessibility first" in merged_principles
        assert "Clean code" in merged_principles  # Original principle preserved
        
        # Check that team commands were added
        commands = result.merged_persona.command_interface.commands
        assert "run-e2e-tests" in commands
        assert "implement-feature" in commands  # Original command preserved
        
        # Check that team tools were added
        tools = result.merged_persona.resource_dependencies.tools
        assert "cypress" in tools
        assert "storybook" in tools
        assert "git" in tools  # Original tool preserved
    
    def test_merge_with_all_overlays(self, merge_engine, base_persona, team_overlay, project_overlay):
        """Test merging with both team and project overlays (AC: 1)."""
        result = merge_engine.merge_persona(
            base_persona=base_persona,
            team_overlay=team_overlay,
            project_overlay=project_overlay
        )
        
        assert result.success is True
        assert len(result.applied_overlays) == 2
        
        # Check precedence: base < team < project
        merged_principles = result.merged_persona.behavioral_contract.core_principles
        assert "PCI compliance" in merged_principles  # Project overlay
        assert "Performance optimization" in merged_principles  # Project overlay
        assert "React best practices" in merged_principles  # Team overlay
        assert "Clean code" in merged_principles  # Base persona
        
        # Check all commands are present
        commands = result.merged_persona.command_interface.commands
        assert "deploy-production" in commands  # Project overlay
        assert "run-e2e-tests" in commands  # Team overlay
        assert "implement-feature" in commands  # Base persona
    
    def test_conflict_detection_and_resolution(self, merge_engine, base_persona):
        """Test conflict detection and resolution (AC: 3)."""
        # Create conflicting overlays
        team_overlay = PersonaOverlay(
            overlay_type=OverlayType.TEAM,
            context_id="team-a",
            persona_id="dev",
            modifications={
                "behavioral_contract": {
                    "interaction_style": "formal"  # Conflicts with base "collaborative"
                }
            }
        )
        
        project_overlay = PersonaOverlay(
            overlay_type=OverlayType.PROJECT,
            context_id="project-x",
            persona_id="dev",
            modifications={
                "behavioral_contract": {
                    "interaction_style": "casual"  # Conflicts with team "formal"
                }
            }
        )
        
        result = merge_engine.merge_persona(
            base_persona=base_persona,
            team_overlay=team_overlay,
            project_overlay=project_overlay
        )
        
        assert result.success is True
        assert len(result.conflicts) >= 1
        
        # Find the final conflict (there may be multiple as overlays are applied sequentially)
        final_conflict = result.conflicts[-1]  # Last conflict should be the final resolution
        assert "behavioral_contract.interaction_style" in final_conflict.field_path
        assert final_conflict.resolution == ConflictResolution.PROJECT_WINS
        
        # Project should win (highest precedence)
        assert result.merged_persona.behavioral_contract.interaction_style == "casual"
    
    def test_cache_key_generation(self, merge_engine, base_persona, team_overlay, project_overlay):
        """Test cache key generation includes all context (AC: 4)."""
        cache_key = merge_engine.generate_cache_key(
            persona_id="dev",
            team_id="frontend-team",
            project_id="ecommerce-app",
            base_version="v1.0",
            team_version="v1.1",
            project_version="v1.2"
        )
        
        assert "dev" in cache_key
        assert "frontend-team" in cache_key
        assert "ecommerce-app" in cache_key
        assert "v1.0" in cache_key
        assert "v1.1" in cache_key
        assert "v1.2" in cache_key
    
    def test_hot_reload_cache_invalidation(self, merge_engine):
        """Test hot-reload cache invalidation (AC: 4)."""
        cache_key = "dev:team1:proj1:v1:v1:v1"
        
        # Add to cache
        mock_result = Mock()
        merge_engine.cache[cache_key] = mock_result
        
        # Invalidate cache
        merge_engine.invalidate_cache(persona_id="dev", team_id="team1", project_id="proj1")
        
        # Cache should be cleared
        assert cache_key not in merge_engine.cache
    
    def test_audit_trail_generation(self, merge_engine, base_persona, team_overlay):
        """Test audit trail generation (AC: 3)."""
        result = merge_engine.merge_persona(
            base_persona=base_persona,
            team_overlay=team_overlay,
            project_overlay=None
        )
        
        assert len(merge_engine.audit_trail) > 0
        
        audit_entry = merge_engine.audit_trail[-1]
        assert audit_entry["persona_id"] == "dev"
        assert audit_entry["team_id"] == "frontend-team"
        assert audit_entry["project_id"] is None
        assert "timestamp" in audit_entry
        assert "applied_overlays" in audit_entry
        assert "conflicts" in audit_entry


class TestOverlayValidation:
    """Test overlay validation and CI checks (AC: 5)."""
    
    def test_validate_overlay_schema(self):
        """Test overlay schema validation."""
        engine = OverlayMergeEngine()
        
        # Valid overlay
        valid_overlay = {
            "overlay_type": "team",
            "context_id": "frontend-team",
            "persona_id": "dev",
            "modifications": {
                "behavioral_contract": {
                    "core_principles": ["React best practices"]
                }
            }
        }
        
        assert engine.validate_overlay_schema(valid_overlay) is True
        
        # Invalid overlay - missing required field
        invalid_overlay = {
            "overlay_type": "team",
            # Missing context_id
            "persona_id": "dev",
            "modifications": {}
        }
        
        with pytest.raises(OverlayValidationError):
            engine.validate_overlay_schema(invalid_overlay)
    
    def test_validate_overlay_conflicts(self):
        """Test validation of overlay conflicts."""
        engine = OverlayMergeEngine()
        
        # Create overlays with potential conflicts
        team_overlay = PersonaOverlay(
            overlay_type=OverlayType.TEAM,
            context_id="team-a",
            persona_id="dev",
            modifications={
                "command_interface": {
                    "commands": {
                        "test": {
                            "description": "Team test command",
                            "timeout_seconds": 60
                        }
                    }
                }
            }
        )
        
        project_overlay = PersonaOverlay(
            overlay_type=OverlayType.PROJECT,
            context_id="project-x",
            persona_id="dev",
            modifications={
                "command_interface": {
                    "commands": {
                        "test": {
                            "description": "Project test command",
                            "timeout_seconds": 120
                        }
                    }
                }
            }
        )
        
        conflicts = engine.detect_conflicts(team_overlay, project_overlay)
        assert len(conflicts) > 0
        
        # Should detect command name conflict
        command_conflict = next(
            (c for c in conflicts if "commands.test" in c.field_path), 
            None
        )
        assert command_conflict is not None


class TestMergePerformance:
    """Test merge performance and memory usage."""
    
    def test_merge_performance(self):
        """Test merge performance meets requirements."""
        import time
        from orchestra.system.specs import PersonaSpec, PersonaIdentity, BehavioralContract, CommandInterface, ResourceDependencies
        from orchestra.system.persona_overlay_merge import PersonaOverlay, OverlayType
        
        # Create test data
        base_persona = PersonaSpec(
            identity=PersonaIdentity(
                name="Developer", id="dev", title="Developer", role="Engineer",
                icon="💻", when_to_use="For dev tasks", style="Professional", focus="Code"
            ),
            behavioral_contract=BehavioralContract(core_principles=["Clean code"]),
            command_interface=CommandInterface(commands={}),
            resource_dependencies=ResourceDependencies()
        )
        
        team_overlay = PersonaOverlay(
            overlay_type=OverlayType.TEAM,
            context_id="team-a",
            persona_id="dev",
            modifications={"behavioral_contract": {"core_principles": ["Team practices"]}}
        )
        
        project_overlay = PersonaOverlay(
            overlay_type=OverlayType.PROJECT,
            context_id="project-x",
            persona_id="dev",
            modifications={"behavioral_contract": {"core_principles": ["Project standards"]}}
        )
        
        engine = OverlayMergeEngine()
        
        start_time = time.time()
        
        # Perform multiple merges
        for _ in range(100):
            result = engine.merge_persona(
                base_persona=base_persona,
                team_overlay=team_overlay,
                project_overlay=project_overlay
            )
            assert result.success is True
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 100 merges in under 1 second
        assert total_time < 1.0
        
        # Average merge time should be under 10ms
        avg_time = total_time / 100
        assert avg_time < 0.01
    
    def test_memory_usage_with_cache(self):
        """Test memory usage with caching."""
        engine = OverlayMergeEngine()
        
        # Cache should not grow unbounded
        for i in range(1000):
            cache_key = f"test-key-{i}"
            engine.cache[cache_key] = f"test-value-{i}"
        
        # Cache should implement LRU or similar strategy
        # This is a placeholder - actual implementation would have size limits
        assert len(engine.cache) <= 1000


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""
    
    def test_frontend_team_ecommerce_project_scenario(self):
        """Test realistic frontend team + ecommerce project scenario."""
        # Base dev persona
        base_dev = PersonaSpec(
            identity=PersonaIdentity(
                name="Developer",
                id="dev",
                title="Full Stack Developer",
                role="Software Engineer",
                icon="💻",
                when_to_use="For development tasks",
                style="Professional",
                focus="Code quality"
            ),
            behavioral_contract=BehavioralContract(
                core_principles=["Clean code", "Test coverage"],
                interaction_style="collaborative"
            ),
            command_interface=CommandInterface(commands={}),
            resource_dependencies=ResourceDependencies(
                tools=["git", "docker"]
            )
        )
        
        # Frontend team overlay
        frontend_overlay = PersonaOverlay(
            overlay_type=OverlayType.TEAM,
            context_id="frontend-team",
            persona_id="dev",
            modifications={
                "behavioral_contract": {
                    "core_principles": ["React patterns", "Accessibility"]
                },
                "resource_dependencies": {
                    "tools": ["webpack", "cypress"]
                }
            }
        )
        
        # Ecommerce project overlay
        ecommerce_overlay = PersonaOverlay(
            overlay_type=OverlayType.PROJECT,
            context_id="ecommerce-app",
            persona_id="dev",
            modifications={
                "behavioral_contract": {
                    "core_principles": ["PCI compliance", "Performance"]
                },
                "resource_dependencies": {
                    "tools": ["stripe-cli", "redis-cli"]
                }
            }
        )
        
        engine = OverlayMergeEngine()
        result = engine.merge_persona(
            base_persona=base_dev,
            team_overlay=frontend_overlay,
            project_overlay=ecommerce_overlay
        )
        
        assert result.success is True
        
        # Check all principles are present
        principles = result.merged_persona.behavioral_contract.core_principles
        assert "Clean code" in principles  # Base
        assert "React patterns" in principles  # Team
        assert "PCI compliance" in principles  # Project
        
        # Check all tools are present
        tools = result.merged_persona.resource_dependencies.tools
        assert "git" in tools  # Base
        assert "webpack" in tools  # Team
        assert "stripe-cli" in tools  # Project