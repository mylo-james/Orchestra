# Security

## Input Validation

- **Validation Library:** Pydantic (backend), Zod (frontend)
- **Validation Location:** API boundary validation before agent processing
- **Required Rules:**
  - All user inputs MUST be validated before agent processing
  - Validation at FastAPI endpoint level with Pydantic models
  - Whitelist approach for allowed file types and code patterns

## Authentication & Authorization

- **Auth Method:** NextAuth.js with GitHub OAuth provider
- **Session Management:** JWT tokens with httpOnly cookies
- **Required Patterns:**
  - GitHub OAuth for repository access and user identity
  - Role-based access control for workflow management
  - API key validation for all backend endpoints

## Secrets Management

- **Development:** Environment variables with .env files
- **Production:** AWS Systems Manager Parameter Store
- **Code Requirements:**
  - NEVER hardcode API keys or tokens
  - Access secrets via configuration service only
  - No secrets in logs, error messages, or agent traces

## API Security

- **Rate Limiting:** 100 requests/minute per user, 10 workflows/hour per user
- **CORS Policy:** Restricted to frontend domains only
- **Security Headers:** HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- **HTTPS Enforcement:** All production traffic requires HTTPS

## Data Protection

- **Encryption at Rest:** AES-256 for sensitive data in PostgreSQL
- **Encryption in Transit:** TLS 1.3 for all external communications
- **PII Handling:** User emails encrypted, no PII in logs or knowledge base
- **Logging Restrictions:** No user tokens, API keys, or personal data in logs

## Dependency Security

- **Scanning Tool:** Dependabot for automated vulnerability scanning
- **Update Policy:** Security updates within 24 hours, other updates weekly
- **Approval Process:** All new dependencies require architecture review

## Security Testing

- **SAST Tool:** CodeQL for code analysis
- **DAST Tool:** OWASP ZAP for runtime security testing
- **Penetration Testing:** Quarterly security assessment of production system
