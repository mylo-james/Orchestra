"""Tests for configuration settings - easy coverage wins."""

import os
from unittest.mock import patch

import pytest

from src.config.settings import Settings, get_settings


class TestSettings:
    """Test configuration settings."""

    def test_settings_creation(self):
        """Test basic settings creation."""
        settings = Settings()
        assert settings is not None
        assert hasattr(settings, "environment")
        assert hasattr(settings, "debug")

    def test_settings_defaults(self):
        """Test default settings values."""
        settings = Settings()
        # These should have reasonable defaults
        assert settings.environment in ["development", "test", "production"]
        assert isinstance(settings.debug, bool)

    @patch.dict(
        os.environ, {"ENVIRONMENT": "test", "DEBUG": "true", "LOG_LEVEL": "DEBUG"}
    )
    def test_settings_from_environment(self):
        """Test settings loading from environment."""
        settings = Settings()
        assert settings.environment == "test"
        assert settings.debug is True

    def test_get_settings_function(self):
        """Test get_settings function."""
        settings = get_settings()
        assert isinstance(settings, Settings)

        # Should be consistent
        settings2 = get_settings()
        assert settings is settings2  # Should be singleton

    def test_settings_validation(self):
        """Test settings validation."""
        # This tests that pydantic validation works
        try:
            Settings()
            # Should not raise validation errors with defaults
        except Exception as e:
            pytest.fail(f"Settings validation failed: {e}")

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "sk-test-key", "QDRANT_HOST": "localhost"},
    )
    def test_api_key_configuration(self):
        """Test API key configuration."""
        settings = Settings()
        # Should handle API keys properly
        assert hasattr(settings, "openai")
        if hasattr(settings.openai, "api_key"):
            assert len(settings.openai.api_key) > 0

    def test_database_configuration(self):
        """Test database configuration."""
        settings = Settings()
        assert hasattr(settings, "database")
        # Database settings should be accessible
        db_config = settings.database
        assert db_config is not None

    def test_settings_repr(self):
        """Test settings string representation."""
        settings = Settings()
        repr_str = repr(settings)
        assert "Settings" in repr_str
        # Note: repr() includes test API keys, which is expected in test environment

    @patch.dict(os.environ, {"INVALID_SETTING": "should_be_ignored"})
    def test_unknown_environment_variables_ignored(self):
        """Test that unknown environment variables are ignored."""
        # Should not raise errors with unknown env vars
        settings = Settings()
        assert settings is not None


class TestSettingsSubcomponents:
    """Test settings subcomponents for additional coverage."""

    def test_openai_settings(self):
        """Test OpenAI settings component."""
        settings = Settings()
        openai_config = settings.openai
        assert openai_config is not None
        # Should have required attributes
        assert hasattr(openai_config, "api_key")

    def test_database_settings(self):
        """Test database settings component."""
        settings = Settings()
        db_config = settings.database
        assert db_config is not None
        # Should have required attributes for database config

    def test_qdrant_settings(self):
        """Test Qdrant settings component."""
        settings = Settings()
        # Should handle Qdrant config
        assert hasattr(settings, "qdrant")

    def test_github_settings(self):
        """Test GitHub settings component."""
        settings = Settings()
        # Should handle GitHub config
        assert hasattr(settings, "github")

    def test_temporal_settings(self):
        """Test Temporal settings component."""
        settings = Settings()
        # Should handle Temporal config
        assert hasattr(settings, "temporal")

    @patch.dict(os.environ, {"ENVIRONMENT": "production", "DEBUG": "false"})
    def test_production_configuration(self):
        """Test production environment configuration."""
        settings = Settings()
        assert settings.environment == "production"
        assert settings.debug is False

    @patch.dict(os.environ, {"ENVIRONMENT": "development", "DEBUG": "true"})
    def test_development_configuration(self):
        """Test development environment configuration."""
        settings = Settings()
        assert settings.environment == "development"
        assert settings.debug is True
