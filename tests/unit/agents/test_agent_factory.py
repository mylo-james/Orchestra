from src.system.factory import get_registry


def test_registry_creates_persona_agents():
    """Test that registry can create persona-based agents."""
    registry = get_registry()

    # Test creating orchestrator persona
    orchestrator = registry.create("orchestrator")
    assert orchestrator is not None
    assert orchestrator.persona_id == "orchestrator"

    # Test creating dev persona
    dev = registry.create("dev")
    assert dev is not None
    assert dev.persona_id == "dev"

    # Test creating release persona
    release = registry.create("release")
    assert release is not None
    assert release.persona_id == "release"


def test_registry_lists_personas():
    """Test that registry can list available personas."""
    registry = get_registry()
    personas = registry.list_personas()

    # Should have at least the core personas
    persona_ids = [p["id"] for p in personas]
    assert "orchestrator" in persona_ids
    assert "dev" in persona_ids
    assert "release" in persona_ids
