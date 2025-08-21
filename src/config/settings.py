"""Secure configuration management with environment variable validation."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="orchestra", description="Database name")
    user: str = Field(default="orchestra", description="Database user")
    password: str = Field(default="orchestra", description="Database password")

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    @property
    def url(self) -> str:
        """Get database URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class TemporalSettings(BaseSettings):
    """Temporal workflow configuration."""

    host: str = Field(default="localhost", description="Temporal server host")
    port: int = Field(default=7233, description="Temporal server port")
    namespace: str = Field(default="default", description="Temporal namespace")
    task_queue: str = Field(default="orchestra-tasks", description="Task queue name")

    model_config = SettingsConfigDict(env_prefix="TEMPORAL_")

    @property
    def address(self) -> str:
        """Get Temporal server address."""
        return f"{self.host}:{self.port}"


class OpenAISettings(BaseSettings):
    """OpenAI API configuration."""

    api_key: str = Field(default="sk-test-key", description="OpenAI API key")
    model: str = Field(default="gpt-4o", description="Primary GPT model")
    embedding_model: str = Field(
        default="text-embedding-3-large", description="Embedding model"
    )
    max_tokens: int = Field(default=4096, description="Maximum tokens per request")
    temperature: float = Field(default=0.1, description="Model temperature")

    model_config = SettingsConfigDict(env_prefix="OPENAI_")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate OpenAI API key format."""
        if not (v.startswith("sk-") or v == "sk-test-key"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v


class PineconeSettings(BaseSettings):
    """Pinecone vector database configuration."""

    api_key: str = Field(default="test-pinecone-key", description="Pinecone API key")
    environment: str = Field(
        default="test-environment", description="Pinecone environment"
    )
    index_name: str = Field(default="orchestra-knowledge", description="Index name")
    dimension: int = Field(
        default=3072, description="Vector dimension for text-embedding-3-large"
    )

    model_config = SettingsConfigDict(env_prefix="PINECONE_")


class GitHubSettings(BaseSettings):
    """GitHub integration configuration."""

    token: str | None = Field(default=None, description="GitHub personal access token")
    org: str | None = Field(default=None, description="GitHub organization")
    repo: str | None = Field(default=None, description="GitHub repository")

    model_config = SettingsConfigDict(env_prefix="GITHUB_")


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    enable_audit_logging: bool = Field(
        default=True, description="Enable security audit logging"
    )
    max_file_size: int = Field(
        default=10_000_000, description="Maximum file size for processing (10MB)"
    )
    allowed_file_extensions: list[str] = Field(
        default=[".py", ".md", ".txt", ".yaml", ".yml", ".json", ".toml"],
        description="Allowed file extensions for code generation",
    )
    enable_code_scanning: bool = Field(
        default=True, description="Enable security code scanning"
    )

    model_config = SettingsConfigDict(env_prefix="SECURITY_")


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    level: str = Field(default="INFO", description="Logging level")
    json_format: bool = Field(default=False, description="Use JSON log format")
    enable_audit: bool = Field(default=True, description="Enable audit logging")

    model_config = SettingsConfigDict(env_prefix="LOG_")

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class Settings(BaseSettings):
    """Main application settings."""

    # Application
    app_name: str = Field(default="Orchestra", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # Component settings
    database: DatabaseSettings = Field(default_factory=lambda: DatabaseSettings())
    temporal: TemporalSettings = Field(default_factory=lambda: TemporalSettings())
    openai: OpenAISettings = Field(default_factory=lambda: OpenAISettings())
    pinecone: PineconeSettings = Field(default_factory=lambda: PineconeSettings())
    github: GitHubSettings = Field(default_factory=lambda: GitHubSettings())
    security: SecuritySettings = Field(default_factory=lambda: SecuritySettings())
    logging: LoggingSettings = Field(default_factory=lambda: LoggingSettings())

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment setting."""
        valid_envs = ["development", "staging", "production", "test"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment == "test"


# Global settings instance (lazy initialization)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
