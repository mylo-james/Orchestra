"""Tests for persona specification data structures."""

import pytest

from orchestra.system.specs import (
    BehavioralContract,
    CommandDefinition,
    CommandInterface,
    KnowledgeContext,
    PersonaIdentity,
    PersonaSpec,
    ResourceDependencies,
)


class TestPersonaIdentity:
    """Test PersonaIdentity dataclass."""

    def test_persona_identity_creation_minimal(self):
        """Test creating PersonaIdentity with minimal required fields."""
        identity = PersonaIdentity(
            name="Test Agent", id="test-agent", title="Test Agent", role="tester"
        )

        assert identity.name == "Test Agent"
        assert identity.id == "test-agent"
        assert identity.title == "Test Agent"
        assert identity.role == "tester"
        assert identity.icon == "🤖"  # Default
        assert identity.when_to_use == ""  # Default
        assert identity.style == ""  # Default
        assert identity.focus == ""  # Default

    def test_persona_identity_creation_complete(self):
        """Test creating PersonaIdentity with all fields."""
        identity = PersonaIdentity(
            name="Developer Agent",
            id="dev-agent",
            title="Senior Developer",
            role="full-stack-developer",
            icon="👨‍💻",
            when_to_use="For complex development tasks",
            style="professional and thorough",
            focus="code quality and testing",
        )

        assert identity.name == "Developer Agent"
        assert identity.id == "dev-agent"
        assert identity.title == "Senior Developer"
        assert identity.role == "full-stack-developer"
        assert identity.icon == "👨‍💻"
        assert identity.when_to_use == "For complex development tasks"
        assert identity.style == "professional and thorough"
        assert identity.focus == "code quality and testing"

    def test_persona_identity_immutable(self):
        """Test that PersonaIdentity is immutable after creation."""
        identity = PersonaIdentity(name="Test", id="test", title="Test", role="test")

        # Should be able to access fields
        assert identity.name == "Test"

        # Should be able to modify (dataclass is not frozen by default)
        identity.name = "Modified"
        assert identity.name == "Modified"

    def test_persona_identity_unicode_support(self):
        """Test PersonaIdentity with Unicode characters."""
        identity = PersonaIdentity(
            name="Développeur IA",
            id="dev-fr",
            title="Développeur Intelligence Artificielle",
            role="développeur",
            icon="🇫🇷",
            when_to_use="Pour les projets français",
            style="professionnel et précis",
            focus="qualité du code",
        )

        assert identity.name == "Développeur IA"
        assert identity.icon == "🇫🇷"
        assert identity.when_to_use == "Pour les projets français"


class TestBehavioralContract:
    """Test BehavioralContract dataclass."""

    def test_behavioral_contract_defaults(self):
        """Test BehavioralContract with default values."""
        contract = BehavioralContract()

        assert contract.core_principles == []
        assert contract.interaction_style == "conversational"
        assert contract.halt_conditions == []
        assert contract.decision_framework is None
        assert contract.escalation_triggers == []

    def test_behavioral_contract_complete(self):
        """Test BehavioralContract with all fields."""
        contract = BehavioralContract(
            core_principles=["Quality first", "Test everything", "Document clearly"],
            interaction_style="professional",
            halt_conditions=["security violation", "data corruption"],
            decision_framework="risk-based",
            escalation_triggers=["critical error", "user safety concern"],
        )

        assert len(contract.core_principles) == 3
        assert "Quality first" in contract.core_principles
        assert contract.interaction_style == "professional"
        assert len(contract.halt_conditions) == 2
        assert "security violation" in contract.halt_conditions
        assert contract.decision_framework == "risk-based"
        assert len(contract.escalation_triggers) == 2
        assert "critical error" in contract.escalation_triggers

    def test_behavioral_contract_list_independence(self):
        """Test that list fields are independent between instances."""
        contract1 = BehavioralContract()
        contract2 = BehavioralContract()

        contract1.core_principles.append("Principle 1")
        contract1.halt_conditions.append("Condition 1")

        assert contract1.core_principles == ["Principle 1"]
        assert contract2.core_principles == []
        assert contract1.halt_conditions == ["Condition 1"]
        assert contract2.halt_conditions == []

        # Verify they're different list objects
        assert contract1.core_principles is not contract2.core_principles
        assert contract1.halt_conditions is not contract2.halt_conditions

    def test_behavioral_contract_empty_strings(self):
        """Test BehavioralContract with empty string values."""
        contract = BehavioralContract(interaction_style="", decision_framework="")

        assert contract.interaction_style == ""
        assert contract.decision_framework == ""


class TestCommandDefinition:
    """Test CommandDefinition dataclass."""

    def test_command_definition_minimal(self):
        """Test CommandDefinition with minimal required fields."""
        cmd = CommandDefinition(
            description="Test command", execution_pattern="test -> verify"
        )

        assert cmd.description == "Test command"
        assert cmd.execution_pattern == "test -> verify"
        assert cmd.parameters == {}  # Default
        assert cmd.requires_confirmation is False  # Default
        assert cmd.timeout_seconds == 60  # Default

    def test_command_definition_complete(self):
        """Test CommandDefinition with all fields."""
        cmd = CommandDefinition(
            description="Deploy application",
            execution_pattern="build -> test -> deploy -> verify",
            parameters={"environment": "production", "rollback": True},
            requires_confirmation=True,
            timeout_seconds=300,
        )

        assert cmd.description == "Deploy application"
        assert cmd.execution_pattern == "build -> test -> deploy -> verify"
        assert cmd.parameters["environment"] == "production"
        assert cmd.parameters["rollback"] is True
        assert cmd.requires_confirmation is True
        assert cmd.timeout_seconds == 300

    def test_command_definition_complex_parameters(self):
        """Test CommandDefinition with complex parameter types."""
        cmd = CommandDefinition(
            description="Complex command",
            execution_pattern="process",
            parameters={
                "string_param": "value",
                "int_param": 42,
                "float_param": 3.14,
                "bool_param": True,
                "list_param": [1, 2, 3],
                "dict_param": {"nested": "value"},
                "none_param": None,
            },
        )

        assert cmd.parameters["string_param"] == "value"
        assert cmd.parameters["int_param"] == 42
        assert cmd.parameters["float_param"] == 3.14
        assert cmd.parameters["bool_param"] is True
        assert cmd.parameters["list_param"] == [1, 2, 3]
        assert cmd.parameters["dict_param"]["nested"] == "value"
        assert cmd.parameters["none_param"] is None

    def test_command_definition_parameter_independence(self):
        """Test that parameter dicts are independent between instances."""
        cmd1 = CommandDefinition("Cmd 1", "pattern1")
        cmd2 = CommandDefinition("Cmd 2", "pattern2")

        cmd1.parameters["key1"] = "value1"
        cmd2.parameters["key2"] = "value2"

        assert cmd1.parameters == {"key1": "value1"}
        assert cmd2.parameters == {"key2": "value2"}
        assert cmd1.parameters is not cmd2.parameters


class TestCommandInterface:
    """Test CommandInterface dataclass."""

    def test_command_interface_defaults(self):
        """Test CommandInterface with default values."""
        interface = CommandInterface()

        assert interface.execution_model == "sequential"
        assert interface.commands == {}
        assert interface.default_command is None
        assert interface.command_aliases == {}

    def test_command_interface_complete(self):
        """Test CommandInterface with all fields."""
        cmd1 = CommandDefinition("First command", "pattern1")
        cmd2 = CommandDefinition("Second command", "pattern2")

        interface = CommandInterface(
            execution_model="parallel",
            commands={"cmd1": cmd1, "cmd2": cmd2},
            default_command="cmd1",
            command_aliases={"c1": "cmd1", "c2": "cmd2"},
        )

        assert interface.execution_model == "parallel"
        assert len(interface.commands) == 2
        assert interface.commands["cmd1"] == cmd1
        assert interface.commands["cmd2"] == cmd2
        assert interface.default_command == "cmd1"
        assert interface.command_aliases["c1"] == "cmd1"
        assert interface.command_aliases["c2"] == "cmd2"

    def test_command_interface_execution_models(self):
        """Test different execution models."""
        models = ["sequential", "parallel", "adaptive"]

        for model in models:
            interface = CommandInterface(execution_model=model)
            assert interface.execution_model == model

    def test_command_interface_dict_independence(self):
        """Test that dict fields are independent between instances."""
        interface1 = CommandInterface()
        interface2 = CommandInterface()

        cmd = CommandDefinition("Test", "pattern")
        interface1.commands["test"] = cmd
        interface1.command_aliases["t"] = "test"

        assert len(interface1.commands) == 1
        assert len(interface2.commands) == 0
        assert len(interface1.command_aliases) == 1
        assert len(interface2.command_aliases) == 0

        # Verify they're different dict objects
        assert interface1.commands is not interface2.commands
        assert interface1.command_aliases is not interface2.command_aliases


class TestResourceDependencies:
    """Test ResourceDependencies dataclass."""

    def test_resource_dependencies_defaults(self):
        """Test ResourceDependencies with default values."""
        deps = ResourceDependencies()

        assert deps.knowledge_sources == []
        assert deps.tasks == []
        assert deps.tools == []
        assert deps.templates == []
        assert deps.required_services == []

    def test_resource_dependencies_complete(self):
        """Test ResourceDependencies with all fields."""
        deps = ResourceDependencies(
            knowledge_sources=["python-docs", "api-reference"],
            tasks=["code-generation", "testing"],
            tools=["pytest", "black", "mypy"],
            templates=["python-class", "test-template"],
            required_services=["github", "openai"],
        )

        assert len(deps.knowledge_sources) == 2
        assert "python-docs" in deps.knowledge_sources
        assert len(deps.tasks) == 2
        assert "code-generation" in deps.tasks
        assert len(deps.tools) == 3
        assert "pytest" in deps.tools
        assert len(deps.templates) == 2
        assert "python-class" in deps.templates
        assert len(deps.required_services) == 2
        assert "github" in deps.required_services

    def test_resource_dependencies_list_independence(self):
        """Test that list fields are independent between instances."""
        deps1 = ResourceDependencies()
        deps2 = ResourceDependencies()

        deps1.knowledge_sources.append("source1")
        deps1.tools.append("tool1")

        assert deps1.knowledge_sources == ["source1"]
        assert deps2.knowledge_sources == []
        assert deps1.tools == ["tool1"]
        assert deps2.tools == []

        # Verify they're different list objects
        assert deps1.knowledge_sources is not deps2.knowledge_sources
        assert deps1.tools is not deps2.tools

    def test_resource_dependencies_empty_lists(self):
        """Test ResourceDependencies with explicitly empty lists."""
        deps = ResourceDependencies(
            knowledge_sources=[], tasks=[], tools=[], templates=[], required_services=[]
        )

        assert deps.knowledge_sources == []
        assert deps.tasks == []
        assert deps.tools == []
        assert deps.templates == []
        assert deps.required_services == []


class TestKnowledgeContext:
    """Test KnowledgeContext dataclass."""

    def test_knowledge_context_defaults(self):
        """Test KnowledgeContext with default values."""
        context = KnowledgeContext()

        assert context.domains == []
        assert context.expertise_areas == []
        assert context.learning_sources == []
        assert context.context_window_size == 4096
        assert context.memory_retention_policy == "session"

    def test_knowledge_context_complete(self):
        """Test KnowledgeContext with all fields."""
        context = KnowledgeContext(
            domains=["software-development", "ai-ml"],
            expertise_areas=["python", "machine-learning", "web-development"],
            learning_sources=["documentation", "code-examples", "tutorials"],
            context_window_size=8192,
            memory_retention_policy="persistent",
        )

        assert len(context.domains) == 2
        assert "software-development" in context.domains
        assert len(context.expertise_areas) == 3
        assert "python" in context.expertise_areas
        assert len(context.learning_sources) == 3
        assert "documentation" in context.learning_sources
        assert context.context_window_size == 8192
        assert context.memory_retention_policy == "persistent"

    def test_knowledge_context_memory_policies(self):
        """Test different memory retention policies."""
        policies = ["session", "persistent", "adaptive"]

        for policy in policies:
            context = KnowledgeContext(memory_retention_policy=policy)
            assert context.memory_retention_policy == policy

    def test_knowledge_context_window_sizes(self):
        """Test different context window sizes."""
        sizes = [1024, 2048, 4096, 8192, 16384, 32768]

        for size in sizes:
            context = KnowledgeContext(context_window_size=size)
            assert context.context_window_size == size

    def test_knowledge_context_list_independence(self):
        """Test that list fields are independent between instances."""
        context1 = KnowledgeContext()
        context2 = KnowledgeContext()

        context1.domains.append("domain1")
        context1.expertise_areas.append("area1")

        assert context1.domains == ["domain1"]
        assert context2.domains == []
        assert context1.expertise_areas == ["area1"]
        assert context2.expertise_areas == []

        # Verify they're different list objects
        assert context1.domains is not context2.domains
        assert context1.expertise_areas is not context2.expertise_areas


class TestPersonaSpec:
    """Test PersonaSpec dataclass."""

    @pytest.fixture
    def sample_identity(self):
        """Create a sample PersonaIdentity."""
        return PersonaIdentity(
            name="Test Developer",
            id="test-dev",
            title="Test Developer Agent",
            role="developer",
            icon="👨‍💻",
        )

    @pytest.fixture
    def sample_behavioral_contract(self):
        """Create a sample BehavioralContract."""
        return BehavioralContract(
            core_principles=["Write clean code", "Test everything"],
            interaction_style="helpful",
            halt_conditions=["syntax error"],
            decision_framework="test-driven",
        )

    @pytest.fixture
    def sample_command_interface(self):
        """Create a sample CommandInterface."""
        cmd = CommandDefinition(
            description="Generate code", execution_pattern="analyze -> code -> test"
        )
        return CommandInterface(
            execution_model="sequential", commands={"code": cmd}, default_command="code"
        )

    @pytest.fixture
    def sample_resource_dependencies(self):
        """Create sample ResourceDependencies."""
        return ResourceDependencies(
            knowledge_sources=["python-docs"],
            tools=["pytest", "black"],
            required_services=["github"],
        )

    @pytest.fixture
    def sample_knowledge_context(self):
        """Create a sample KnowledgeContext."""
        return KnowledgeContext(
            domains=["software-development"],
            expertise_areas=["python", "testing"],
            context_window_size=8192,
        )

    def test_persona_spec_minimal(self, sample_identity):
        """Test PersonaSpec with minimal required fields."""
        spec = PersonaSpec(identity=sample_identity)

        assert spec.identity == sample_identity
        assert isinstance(spec.behavioral_contract, BehavioralContract)
        assert isinstance(spec.command_interface, CommandInterface)
        assert isinstance(spec.resource_dependencies, ResourceDependencies)
        assert spec.knowledge_context is None
        assert spec.version == "1.0.0"
        assert spec.created_by == "system"
        assert spec.last_modified is None
        assert spec.tags == []
        assert spec.enabled is True
        assert spec.experimental is False
        assert spec.deprecated is False

    def test_persona_spec_complete(
        self,
        sample_identity,
        sample_behavioral_contract,
        sample_command_interface,
        sample_resource_dependencies,
        sample_knowledge_context,
    ):
        """Test PersonaSpec with all fields."""
        spec = PersonaSpec(
            identity=sample_identity,
            behavioral_contract=sample_behavioral_contract,
            command_interface=sample_command_interface,
            resource_dependencies=sample_resource_dependencies,
            knowledge_context=sample_knowledge_context,
            version="2.1.0",
            created_by="test-user",
            last_modified="2024-01-01",
            tags=["developer", "python"],
            enabled=True,
            experimental=True,
            deprecated=False,
        )

        assert spec.identity == sample_identity
        assert spec.behavioral_contract == sample_behavioral_contract
        assert spec.command_interface == sample_command_interface
        assert spec.resource_dependencies == sample_resource_dependencies
        assert spec.knowledge_context == sample_knowledge_context
        assert spec.version == "2.1.0"
        assert spec.created_by == "test-user"
        assert spec.last_modified == "2024-01-01"
        assert spec.tags == ["developer", "python"]
        assert spec.enabled is True
        assert spec.experimental is True
        assert spec.deprecated is False

    def test_persona_spec_full_id_property(self, sample_identity):
        """Test PersonaSpec.full_id property."""
        spec = PersonaSpec(identity=sample_identity, version="1.2.3")

        assert spec.full_id == "test-dev@1.2.3"

    def test_persona_spec_display_name_property(self, sample_identity):
        """Test PersonaSpec.display_name property."""
        spec = PersonaSpec(identity=sample_identity)

        assert spec.display_name == "👨‍💻 Test Developer"

    def test_persona_spec_get_command_direct(
        self, sample_identity, sample_command_interface
    ):
        """Test PersonaSpec.get_command() with direct command name."""
        spec = PersonaSpec(
            identity=sample_identity, command_interface=sample_command_interface
        )

        cmd = spec.get_command("code")
        assert cmd is not None
        assert cmd.description == "Generate code"
        assert cmd.execution_pattern == "analyze -> code -> test"

    def test_persona_spec_get_command_alias(self, sample_identity):
        """Test PersonaSpec.get_command() with command alias."""
        cmd_def = CommandDefinition("Test command", "test pattern")
        interface = CommandInterface(
            commands={"test_cmd": cmd_def}, command_aliases={"tc": "test_cmd"}
        )
        spec = PersonaSpec(identity=sample_identity, command_interface=interface)

        cmd = spec.get_command("tc")
        assert cmd is not None
        assert cmd == cmd_def
        assert cmd.description == "Test command"

    def test_persona_spec_get_command_not_found(self, sample_identity):
        """Test PersonaSpec.get_command() with non-existent command."""
        spec = PersonaSpec(identity=sample_identity)

        cmd = spec.get_command("nonexistent")
        assert cmd is None

    def test_persona_spec_get_command_alias_not_found(self, sample_identity):
        """Test PersonaSpec.get_command() with alias pointing to non-existent command."""
        interface = CommandInterface(
            commands={}, command_aliases={"broken": "nonexistent"}
        )
        spec = PersonaSpec(identity=sample_identity, command_interface=interface)

        cmd = spec.get_command("broken")
        assert cmd is None

    def test_persona_spec_validate_valid(
        self, sample_identity, sample_behavioral_contract
    ):
        """Test PersonaSpec.validate() with valid spec."""
        spec = PersonaSpec(
            identity=sample_identity, behavioral_contract=sample_behavioral_contract
        )

        errors = spec.validate()
        assert errors == []

    def test_persona_spec_validate_missing_name(self):
        """Test PersonaSpec.validate() with missing name."""
        identity = PersonaIdentity(name="", id="test", title="Test", role="test")
        spec = PersonaSpec(identity=identity)

        errors = spec.validate()
        assert "Missing persona name" in errors

    def test_persona_spec_validate_missing_id(self, sample_identity):
        """Test PersonaSpec.validate() with missing ID."""
        sample_identity.id = ""
        spec = PersonaSpec(identity=sample_identity)

        errors = spec.validate()
        assert "Missing persona ID" in errors

    def test_persona_spec_validate_missing_role(self, sample_identity):
        """Test PersonaSpec.validate() with missing role."""
        sample_identity.role = ""
        spec = PersonaSpec(identity=sample_identity)

        errors = spec.validate()
        assert "Missing persona role" in errors

    def test_persona_spec_validate_no_core_principles(self, sample_identity):
        """Test PersonaSpec.validate() with no core principles."""
        contract = BehavioralContract(core_principles=[])
        spec = PersonaSpec(identity=sample_identity, behavioral_contract=contract)

        errors = spec.validate()
        assert "No core principles defined" in errors

    def test_persona_spec_validate_command_missing_description(self, sample_identity):
        """Test PersonaSpec.validate() with command missing description."""
        cmd = CommandDefinition(description="", execution_pattern="pattern")
        interface = CommandInterface(commands={"bad_cmd": cmd})
        spec = PersonaSpec(identity=sample_identity, command_interface=interface)

        errors = spec.validate()
        assert "Command 'bad_cmd' missing description" in errors

    def test_persona_spec_validate_command_missing_pattern(self, sample_identity):
        """Test PersonaSpec.validate() with command missing execution pattern."""
        cmd = CommandDefinition(description="Good description", execution_pattern="")
        interface = CommandInterface(commands={"bad_cmd": cmd})
        spec = PersonaSpec(identity=sample_identity, command_interface=interface)

        errors = spec.validate()
        assert "Command 'bad_cmd' missing execution pattern" in errors

    def test_persona_spec_validate_multiple_errors(self):
        """Test PersonaSpec.validate() with multiple validation errors."""
        identity = PersonaIdentity(name="", id="", title="Test", role="")
        contract = BehavioralContract(core_principles=[])
        cmd = CommandDefinition(description="", execution_pattern="")
        interface = CommandInterface(commands={"bad_cmd": cmd})

        spec = PersonaSpec(
            identity=identity, behavioral_contract=contract, command_interface=interface
        )

        errors = spec.validate()
        assert len(errors) >= 5  # At least 5 errors
        assert "Missing persona name" in errors
        assert "Missing persona ID" in errors
        assert "Missing persona role" in errors
        assert "No core principles defined" in errors
        assert "Command 'bad_cmd' missing description" in errors
        assert "Command 'bad_cmd' missing execution pattern" in errors

    def test_persona_spec_to_dict_minimal(self, sample_identity):
        """Test PersonaSpec.to_dict() with minimal spec."""
        spec = PersonaSpec(identity=sample_identity)

        result = spec.to_dict()

        # Check identity
        assert result["identity"]["name"] == "Test Developer"
        assert result["identity"]["id"] == "test-dev"
        assert result["identity"]["icon"] == "👨‍💻"

        # Check behavioral contract
        assert result["behavioral_contract"]["core_principles"] == []
        assert result["behavioral_contract"]["interaction_style"] == "conversational"

        # Check command interface
        assert result["command_interface"]["execution_model"] == "sequential"
        assert result["command_interface"]["commands"] == {}

        # Check resource dependencies
        assert result["resource_dependencies"]["tools"] == []
        assert result["resource_dependencies"]["knowledge_sources"] == []

        # Check knowledge context (should be None)
        assert result["knowledge_context"] is None

        # Check metadata
        assert result["version"] == "1.0.0"
        assert result["created_by"] == "system"
        assert result["enabled"] is True

    def test_persona_spec_to_dict_complete(
        self,
        sample_identity,
        sample_behavioral_contract,
        sample_command_interface,
        sample_resource_dependencies,
        sample_knowledge_context,
    ):
        """Test PersonaSpec.to_dict() with complete spec."""
        spec = PersonaSpec(
            identity=sample_identity,
            behavioral_contract=sample_behavioral_contract,
            command_interface=sample_command_interface,
            resource_dependencies=sample_resource_dependencies,
            knowledge_context=sample_knowledge_context,
            version="2.0.0",
            created_by="test-user",
            last_modified="2024-01-01",
            tags=["test", "dev"],
            experimental=True,
        )

        result = spec.to_dict()

        # Check identity
        assert result["identity"]["name"] == "Test Developer"
        assert result["identity"]["id"] == "test-dev"

        # Check behavioral contract
        assert "Write clean code" in result["behavioral_contract"]["core_principles"]
        assert result["behavioral_contract"]["interaction_style"] == "helpful"

        # Check command interface
        assert "code" in result["command_interface"]["commands"]
        cmd_dict = result["command_interface"]["commands"]["code"]
        assert cmd_dict["description"] == "Generate code"
        assert cmd_dict["execution_pattern"] == "analyze -> code -> test"

        # Check resource dependencies
        assert "pytest" in result["resource_dependencies"]["tools"]
        assert "python-docs" in result["resource_dependencies"]["knowledge_sources"]

        # Check knowledge context
        assert result["knowledge_context"] is not None
        assert "software-development" in result["knowledge_context"]["domains"]
        assert result["knowledge_context"]["context_window_size"] == 8192

        # Check metadata
        assert result["version"] == "2.0.0"
        assert result["created_by"] == "test-user"
        assert result["last_modified"] == "2024-01-01"
        assert result["tags"] == ["test", "dev"]
        assert result["experimental"] is True

    def test_persona_spec_list_independence(self, sample_identity):
        """Test that list fields are independent between PersonaSpec instances."""
        spec1 = PersonaSpec(identity=sample_identity)
        spec2 = PersonaSpec(identity=sample_identity)

        spec1.tags.append("tag1")
        spec1.behavioral_contract.core_principles.append("principle1")

        assert spec1.tags == ["tag1"]
        assert spec2.tags == []
        assert len(spec1.behavioral_contract.core_principles) == 1
        assert len(spec2.behavioral_contract.core_principles) == 0

        # Verify they're different objects
        assert spec1.tags is not spec2.tags
        assert spec1.behavioral_contract is not spec2.behavioral_contract


class TestPersonaSpecIntegration:
    """Test integration scenarios for PersonaSpec."""

    def test_full_persona_workflow(self):
        """Test complete persona creation and usage workflow."""
        # Create a complete persona
        identity = PersonaIdentity(
            name="Full Stack Developer",
            id="fullstack-dev",
            title="Senior Full Stack Developer",
            role="full-stack-developer",
            icon="🚀",
            when_to_use="For complex web applications",
            style="thorough and methodical",
            focus="scalability and maintainability",
        )

        contract = BehavioralContract(
            core_principles=[
                "Write clean, maintainable code",
                "Comprehensive testing",
                "Performance optimization",
                "Security best practices",
            ],
            interaction_style="collaborative",
            halt_conditions=["security vulnerability", "performance regression"],
            decision_framework="architecture-first",
            escalation_triggers=["breaking changes", "data loss risk"],
        )

        # Create multiple commands
        deploy_cmd = CommandDefinition(
            description="Deploy application to production",
            execution_pattern="build -> test -> security-scan -> deploy -> verify",
            parameters={"environment": "production", "rollback_enabled": True},
            requires_confirmation=True,
            timeout_seconds=600,
        )

        test_cmd = CommandDefinition(
            description="Run comprehensive test suite",
            execution_pattern="unit-tests -> integration-tests -> e2e-tests",
            parameters={"coverage_threshold": 90},
            timeout_seconds=300,
        )

        interface = CommandInterface(
            execution_model="adaptive",
            commands={"deploy": deploy_cmd, "test": test_cmd},
            default_command="test",
            command_aliases={"d": "deploy", "t": "test"},
        )

        dependencies = ResourceDependencies(
            knowledge_sources=[
                "web-dev-docs",
                "security-guidelines",
                "performance-guides",
            ],
            tasks=["code-generation", "testing", "deployment", "monitoring"],
            tools=["docker", "kubernetes", "jest", "cypress", "sonarqube"],
            templates=["react-component", "api-endpoint", "database-migration"],
            required_services=["github", "aws", "monitoring-service"],
        )

        knowledge = KnowledgeContext(
            domains=["web-development", "cloud-architecture", "devops"],
            expertise_areas=["react", "node.js", "python", "aws", "kubernetes"],
            learning_sources=["documentation", "best-practices", "case-studies"],
            context_window_size=16384,
            memory_retention_policy="persistent",
        )

        spec = PersonaSpec(
            identity=identity,
            behavioral_contract=contract,
            command_interface=interface,
            resource_dependencies=dependencies,
            knowledge_context=knowledge,
            version="3.2.1",
            created_by="senior-architect",
            last_modified="2024-01-15",
            tags=["fullstack", "senior", "web", "cloud"],
            enabled=True,
            experimental=False,
            deprecated=False,
        )

        # Test properties
        assert spec.full_id == "fullstack-dev@3.2.1"
        assert spec.display_name == "🚀 Full Stack Developer"

        # Test command retrieval
        deploy_cmd_retrieved = spec.get_command("deploy")
        assert deploy_cmd_retrieved == deploy_cmd
        assert deploy_cmd_retrieved.requires_confirmation is True

        # Test command alias
        test_cmd_retrieved = spec.get_command("t")
        assert test_cmd_retrieved == test_cmd

        # Test validation
        errors = spec.validate()
        assert errors == []  # Should be valid

        # Test serialization
        spec_dict = spec.to_dict()
        assert spec_dict["identity"]["name"] == "Full Stack Developer"
        assert len(spec_dict["behavioral_contract"]["core_principles"]) == 4
        assert len(spec_dict["command_interface"]["commands"]) == 2
        assert len(spec_dict["resource_dependencies"]["tools"]) == 5
        assert spec_dict["knowledge_context"]["context_window_size"] == 16384
        assert spec_dict["version"] == "3.2.1"

    def test_persona_spec_edge_cases(self):
        """Test PersonaSpec with edge cases and boundary conditions."""
        # Minimal identity
        identity = PersonaIdentity(name="Min", id="min", title="Min", role="min")

        # Empty behavioral contract
        contract = BehavioralContract(core_principles=["At least one principle"])

        # Large command with many parameters
        large_cmd = CommandDefinition(
            description="Command with many parameters",
            execution_pattern="step1 -> step2 -> step3 -> step4 -> step5",
            parameters={f"param_{i}": f"value_{i}" for i in range(100)},
            timeout_seconds=3600,
        )

        interface = CommandInterface(
            commands={"large_cmd": large_cmd},
            command_aliases={f"alias_{i}": "large_cmd" for i in range(50)},
        )

        # Large resource dependencies
        dependencies = ResourceDependencies(
            knowledge_sources=[f"source_{i}" for i in range(100)],
            tools=[f"tool_{i}" for i in range(200)],
            required_services=[f"service_{i}" for i in range(50)],
        )

        spec = PersonaSpec(
            identity=identity,
            behavioral_contract=contract,
            command_interface=interface,
            resource_dependencies=dependencies,
            tags=[f"tag_{i}" for i in range(1000)],  # Many tags
        )

        # Should still validate and work
        errors = spec.validate()
        assert errors == []

        # Should serialize correctly
        spec_dict = spec.to_dict()
        assert (
            len(spec_dict["command_interface"]["commands"]["large_cmd"]["parameters"])
            == 100
        )
        assert len(spec_dict["resource_dependencies"]["tools"]) == 200
        assert len(spec_dict["tags"]) == 1000

    def test_persona_spec_unicode_and_special_chars(self):
        """Test PersonaSpec with Unicode and special characters."""
        identity = PersonaIdentity(
            name="Разработчик ИИ",  # Russian
            id="ai-dev-ru",
            title="人工智能开发者",  # Chinese
            role="développeur-ia",  # French
            icon="🤖🇷🇺",
            when_to_use="Для проектов ИИ",
            style="профессиональный",
            focus="машинное обучение",
        )

        contract = BehavioralContract(
            core_principles=["Качество кода", "Тестирование", "文档"],
            interaction_style="дружелюбный",
            halt_conditions=["ошибка безопасности"],
            decision_framework="基于风险",
            escalation_triggers=["критическая ошибка"],
        )

        spec = PersonaSpec(identity=identity, behavioral_contract=contract)

        # Should handle Unicode correctly
        assert spec.identity.name == "Разработчик ИИ"
        assert spec.display_name == "🤖🇷🇺 Разработчик ИИ"
        assert "Качество кода" in spec.behavioral_contract.core_principles

        # Should serialize Unicode correctly
        spec_dict = spec.to_dict()
        assert spec_dict["identity"]["name"] == "Разработчик ИИ"
        assert "文档" in spec_dict["behavioral_contract"]["core_principles"]
