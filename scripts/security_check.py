#!/usr/bin/env python3
"""Security validation script for Orchestra."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

# Add orchestra to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "orchestra"))

from orchestra.config.settings import get_settings
from orchestra.utils.logging import SecurityAuditLogger, configure_logging, get_logger

logger = get_logger(__name__)
audit_logger = SecurityAuditLogger("orchestra.security.check")


def run_bandit_scan() -> Dict[str, Any]:
    """Run Bandit security scan on the codebase."""
    print("🔒 Running Bandit security scan...")

    try:
        # Run Bandit with JSON output
        result = subprocess.run(
            [
                "poetry",
                "run",
                "bandit",
                "-r",
                "orchestra/",
                "-f",
                "json",
                "-c",
                "bandit.yaml",
            ],
            capture_output=True,
            text=True,
        )

        if result.stdout:
            scan_results = json.loads(result.stdout)

            # Log security scan results
            audit_logger.log_security_event(
                "security_scan_completed",
                {
                    "tool": "bandit",
                    "issues_found": len(scan_results.get("results", [])),
                    "scan_status": "completed",
                },
            )

            return scan_results
        else:
            print("✅ No security issues found by Bandit")
            return {
                "results": [],
                "metrics": {"_totals": {"nosec": 0, "skipped_tests": 0}},
            }

    except subprocess.CalledProcessError as e:
        print(f"❌ Bandit scan failed: {e}")
        return {"error": str(e)}
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse Bandit output: {e}")
        return {"error": f"JSON parse error: {e}"}


def check_environment_security() -> Dict[str, Any]:
    """Check environment configuration for security issues."""
    print("🔍 Checking environment security...")

    issues = []

    try:
        settings = get_settings()

        # Check if running in production with debug enabled
        if settings.environment == "production" and settings.debug:
            issues.append(
                {
                    "severity": "HIGH",
                    "issue": "Debug mode enabled in production",
                    "recommendation": "Set DEBUG=false in production",
                }
            )

        # Check API key format (basic validation)
        if not settings.openai.api_key.startswith("sk-"):
            issues.append(
                {
                    "severity": "MEDIUM",
                    "issue": "Invalid OpenAI API key format",
                    "recommendation": "Ensure API key starts with 'sk-'",
                }
            )

        # Check if default passwords are being used
        if settings.database.password in ["password", "admin", "123456"]:
            issues.append(
                {
                    "severity": "HIGH",
                    "issue": "Weak database password detected",
                    "recommendation": "Use a strong, unique password",
                }
            )

        # Log environment security check
        audit_logger.log_security_event(
            "environment_security_check",
            {
                "issues_found": len(issues),
                "environment": settings.environment,
                "debug_enabled": settings.debug,
            },
        )

        return {"issues": issues}

    except Exception as e:
        logger.error("Environment security check failed", error=str(e), exc_info=True)
        return {"error": str(e)}


def check_file_permissions() -> Dict[str, Any]:
    """Check file permissions for security issues."""
    print("🔐 Checking file permissions...")

    issues = []
    sensitive_files = [".env", "bandit.yaml", "docker-compose.yml", "pyproject.toml"]

    try:
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                mode = oct(stat.st_mode)[-3:]

                # Check if file is world-readable or world-writable
                if mode[2] in ["4", "5", "6", "7"]:  # World-readable
                    issues.append(
                        {
                            "severity": "MEDIUM",
                            "issue": f"File {file_path} is world-readable (mode: {mode})",
                            "recommendation": f"Run: chmod 600 {file_path}",
                        }
                    )

                if mode[2] in ["2", "3", "6", "7"]:  # World-writable
                    issues.append(
                        {
                            "severity": "HIGH",
                            "issue": f"File {file_path} is world-writable (mode: {mode})",
                            "recommendation": f"Run: chmod 600 {file_path}",
                        }
                    )

        return {"issues": issues}

    except Exception as e:
        logger.error("File permissions check failed", error=str(e), exc_info=True)
        return {"error": str(e)}


def check_secrets_in_code() -> Dict[str, Any]:
    """Check for hardcoded secrets in the codebase."""
    print("🕵️ Checking for hardcoded secrets...")

    issues = []
    secret_patterns = [
        (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
        (r"qdrant-[a-zA-Z0-9-]{20,}", "Qdrant Auth Token"),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded Password"),
        (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded Secret"),
        (r"token\s*=\s*['\"][^'\"]+['\"]", "Hardcoded Token"),
    ]

    try:
        # Scan Python files
        for py_file in Path("orchestra").rglob("*.py"):
            if py_file.is_file():
                content = py_file.read_text()

                for pattern, secret_type in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        issues.append(
                            {
                                "severity": "HIGH",
                                "issue": f"Potential {secret_type} found in {py_file}",
                                "line": content[: match.start()].count("\n") + 1,
                                "recommendation": "Remove hardcoded secret and use environment variables",
                            }
                        )

        # Log secrets check
        audit_logger.log_security_event(
            "secrets_scan_completed",
            {
                "files_scanned": len(list(Path("orchestra").rglob("*.py"))),
                "secrets_found": len(issues),
            },
        )

        return {"issues": issues}

    except Exception as e:
        logger.error("Secrets check failed", error=str(e), exc_info=True)
        return {"error": str(e)}


def check_dependency_security() -> Dict[str, Any]:
    """Check dependencies for known security vulnerabilities."""
    print("📦 Checking dependency security...")

    try:
        # Run pip-audit check
        result = subprocess.run(
            ["poetry", "run", "pip-audit", "--format=json"],
            capture_output=True,
            text=True,
        )

        if result.stdout:
            try:
                audit_results = json.loads(result.stdout)
                return {"vulnerabilities": audit_results}
            except json.JSONDecodeError:
                # pip-audit might output non-JSON when no issues found
                return {"vulnerabilities": []}
        else:
            return {"vulnerabilities": []}

    except subprocess.CalledProcessError as e:
        # pip-audit not installed or other error
        return {"error": f"Dependency security check failed: {e}"}
    except Exception as e:
        logger.error("Dependency security check failed", error=str(e), exc_info=True)
        return {"error": str(e)}


def generate_security_report(results: Dict[str, Any]) -> None:
    """Generate a comprehensive security report."""
    print("\n📊 Security Report")
    print("=" * 50)

    total_issues = 0
    high_severity_issues = 0

    for check_name, check_results in results.items():
        if "error" in check_results:
            print(f"\n❌ {check_name}: {check_results['error']}")
            continue

        issues = check_results.get("issues", [])
        if check_name == "bandit_scan":
            issues = check_results.get("results", [])
        elif check_name == "dependency_security":
            vulnerabilities = check_results.get("vulnerabilities", [])
            # Handle both formats: list of vulnerabilities or audit report
            if isinstance(vulnerabilities, list):
                issues = vulnerabilities
            else:
                issues = (
                    vulnerabilities.get("vulnerabilities", [])
                    if vulnerabilities
                    else []
                )

        if issues:
            print(f"\n⚠️  {check_name}: {len(issues)} issues found")
            total_issues += len(issues)

            for issue in issues[:5]:  # Show first 5 issues
                severity = issue.get("issue_severity", issue.get("severity", "UNKNOWN"))
                if severity == "HIGH":
                    high_severity_issues += 1

                issue_text = issue.get("issue_text", issue.get("issue", str(issue)))
                print(f"  - {severity}: {issue_text}")

            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more issues")
        else:
            print(f"\n✅ {check_name}: No issues found")

    print("\n📈 Summary:")
    print(f"  Total Issues: {total_issues}")
    print(f"  High Severity: {high_severity_issues}")

    if total_issues == 0:
        print("\n🎉 No security issues detected!")
    elif high_severity_issues > 0:
        print(
            f"\n🚨 {high_severity_issues} high severity issues require immediate attention!"
        )
    else:
        print(f"\n⚠️  {total_issues} issues found - please review and address.")


def main():
    """Main security check function."""
    print("🎼 Orchestra Security Check")
    print("=" * 30)

    try:
        # Configure logging
        configure_logging(log_level="INFO", json_logs=False, enable_audit=True)

        # Run all security checks
        results = {
            "bandit_scan": run_bandit_scan(),
            "environment_security": check_environment_security(),
            "file_permissions": check_file_permissions(),
            "secrets_in_code": check_secrets_in_code(),
            "dependency_security": check_dependency_security(),
        }

        # Generate report
        generate_security_report(results)

        # Log overall security check completion
        audit_logger.log_security_event(
            "security_check_completed",
            {"checks_run": len(results), "status": "completed"},
        )

    except KeyboardInterrupt:
        print("\n❌ Security check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Security check failed: {e}")
        logger.error("Security check failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
