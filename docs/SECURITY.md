# Security Best Practices

This document outlines security best practices for developing, deploying, and maintaining this application.

## Table of Contents

- [Authentication & Authorization](#authentication--authorization)
- [Data Protection](#data-protection)
- [API Security](#api-security)
- [Dependency Management](#dependency-management)
- [Secrets Management](#secrets-management)
- [Security Headers](#security-headers)
- [Monitoring & Logging](#monitoring--logging)
- [Incident Response](#incident-response)

## Authentication & Authorization

### Certificate-Based Authentication

✅ **DO:**
- Store certificates in Azure Key Vault
- Use Managed Identity to access certificates
- Implement certificate rotation strategy
- Monitor certificate expiration dates
- Use strong key algorithms (RSA 2048+)

❌ **DON'T:**
- Commit certificates to source control
- Store certificates in plain text
- Use expired certificates
- Share certificates across environments

### JWT Token Validation

✅ **DO:**
```python
# Validate all JWT claims
claims = jwt.decode(
    token,
    key,
    algorithms=["RS256"],
    audience=settings.api_app_id_uri,
    issuer=settings.token_issuer,
)

# Verify required scopes
required_scope = "access_as_user"
if required_scope not in claims.get("scp", "").split():
    raise AuthorizationError("Missing required scope")
```

❌ **DON'T:**
- Skip signature verification
- Ignore token expiration
- Accept tokens from unknown issuers
- Trust unverified claims

## Data Protection

### Input Validation

✅ **DO:**
```python
from pydantic import BaseModel, Field, validator

class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    
    @validator('title', 'content')
    def sanitize_input(cls, v):
        # Remove potentially dangerous characters
        return v.strip()
```

### SQL Injection Prevention

✅ **DO:**
```python
# Use parameterized queries (SQLModel/SQLAlchemy)
statement = select(User).where(User.oid == user_oid)
user = session.exec(statement).first()
```

❌ **DON'T:**
```python
# Never use string formatting for SQL
query = f"SELECT * FROM users WHERE oid = '{user_oid}'"  # VULNERABLE!
```

### XSS Prevention

✅ **DO:**
- Validate and sanitize all user inputs
- Use Content Security Policy headers
- Encode output data
- Use framework security features

### Sensitive Data

✅ **DO:**
- Encrypt sensitive data at rest
- Use TLS for data in transit
- Implement field-level encryption
- Follow data minimization principles

❌ **DON'T:**
- Log sensitive information (passwords, tokens, PII)
- Store plaintext passwords
- Expose internal IDs in URLs
- Return sensitive data in error messages

## API Security

### Rate Limiting

Implement rate limiting to prevent abuse:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/posts")
@limiter.limit("100/minute")
async def list_posts():
    # Implementation
```

### CORS Configuration

✅ **DO:**
```python
# Restrict CORS to known origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

❌ **DON'T:**
```python
# Never use wildcard in production
allow_origins=["*"]  # INSECURE!
```

### Request Size Limits

```python
# Limit request body size
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_request_size=10 * 1024 * 1024  # 10MB
)
```

## Dependency Management

### Regular Updates

```bash
# Check for vulnerabilities
poetry run safety check

# Update dependencies
poetry update

# Audit with Snyk
snyk test
```

### Dependency Scanning

Add to CI/CD pipeline:

```yaml
- name: Security Scan
  run: |
    poetry run safety check
    poetry run bandit -r src
```

### Pin Dependencies

```toml
[tool.poetry.dependencies]
fastapi = "^0.115.0"  # Pin major version
uvicorn = "0.32.0"    # Pin exact version for critical deps
```

## Secrets Management

### Environment Variables

✅ **DO:**
```bash
# Use environment variables
export TENANT_ID="your-tenant-id"
export API_APP_ID_URI="api://your-app-id"
```

### Azure Key Vault

✅ **DO:**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Use managed identity in production
credential = DefaultAzureCredential()
client = SecretClient(vault_url=vault_url, credential=credential)
secret = client.get_secret("database-password")
```

### Local Development

```bash
# Use .env files for local development
cp .env.example .env
# Add .env to .gitignore
```

❌ **DON'T:**
- Commit secrets to Git
- Hardcode secrets in code
- Share secrets via chat/email
- Use production secrets in development

## Security Headers

Implemented in `SecurityHeadersMiddleware`:

```python
# Prevent MIME type sniffing
X-Content-Type-Options: nosniff

# Prevent clickjacking
X-Frame-Options: DENY

# Enable XSS protection
X-XSS-Protection: 1; mode=block

# Enforce HTTPS
Strict-Transport-Security: max-age=31536000; includeSubDomains

# Content Security Policy
Content-Security-Policy: default-src 'self'

# Referrer policy
Referrer-Policy: strict-origin-when-cross-origin
```

## Monitoring & Logging

### Structured Logging

✅ **DO:**
```python
logger.info(
    "User action",
    extra={
        "user_id": user.id,
        "action": "create_post",
        "resource_id": post.id,
        "correlation_id": correlation_id,
    }
)
```

❌ **DON'T:**
```python
# Never log sensitive data
logger.info(f"User {user.email} with password {password}")  # BAD!
```

### Security Monitoring

Monitor for:
- Failed authentication attempts
- Unusual access patterns
- Rate limit violations
- Authorization failures
- Certificate expiration

### Audit Trails

```python
@app.middleware("http")
async def audit_log(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    audit_logger.info(
        "API Request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration": duration,
            "user_id": getattr(request.state, "user_id", None),
            "ip": request.client.host,
        }
    )
    return response
```

## Incident Response

### Security Incident Checklist

1. **Detect**
   - Monitor alerts and logs
   - Identify anomalies
   - Assess severity

2. **Contain**
   - Isolate affected systems
   - Revoke compromised credentials
   - Block malicious IPs

3. **Investigate**
   - Review logs and audit trails
   - Identify root cause
   - Document findings

4. **Remediate**
   - Apply patches/fixes
   - Rotate compromised secrets
   - Update security controls

5. **Recover**
   - Restore from backups
   - Verify system integrity
   - Resume normal operations

6. **Review**
   - Conduct post-mortem
   - Update procedures
   - Implement improvements

### Emergency Contacts

Maintain list of:
- Security team contacts
- Cloud provider support
- Third-party security services
- Legal/compliance contacts

## Security Checklist

### Development

- [ ] Input validation on all user inputs
- [ ] Output encoding to prevent XSS
- [ ] Parameterized queries to prevent SQL injection
- [ ] Proper error handling (no sensitive data in errors)
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] Rate limiting implemented
- [ ] Authentication on all protected endpoints
- [ ] Authorization checks for sensitive operations

### Deployment

- [ ] TLS/HTTPS enforced
- [ ] Certificates stored in Key Vault
- [ ] Environment variables configured
- [ ] Secrets not in source control
- [ ] Security scanning in CI/CD
- [ ] Dependency vulnerabilities checked
- [ ] Logging and monitoring enabled
- [ ] Backup and recovery tested
- [ ] Security headers verified
- [ ] Penetration testing performed

### Operations

- [ ] Regular security updates
- [ ] Certificate rotation strategy
- [ ] Access reviews performed
- [ ] Logs monitored for threats
- [ ] Incident response plan tested
- [ ] Backup verification
- [ ] Disaster recovery drills
- [ ] Security training for team

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Microsoft Security Best Practices](https://docs.microsoft.com/en-us/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public GitHub issue
2. Email security@yourdomain.com with details
3. Include steps to reproduce
4. Allow 90 days for response
5. Coordinate disclosure timing

We appreciate responsible disclosure and will acknowledge your contribution.
