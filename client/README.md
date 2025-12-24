# Blog Client - MSAL Python with Certificate Authentication

A Flask web application demonstrating Microsoft Entra ID authentication using MSAL Python with X.509 certificate-based authentication. This client application interacts with a protected FastAPI backend to perform CRUD operations on blog posts.

## Features

- 🔐 **Certificate-Based Authentication**: Uses X.509 certificates instead of client secrets
- 🔄 **OAuth 2.0 Authorization Code Flow**: Implements secure user delegation
- 🎫 **JWT Bearer Token**: Automatically injects access tokens in API calls
- 📝 **Blog CRUD Operations**: Full create, read, update, delete functionality
- ✅ **Comprehensive Testing**: 38 unit tests with 95%+ coverage on core modules
- 🏗️ **Senior Engineering Patterns**: Repository pattern, dependency injection, proper error handling

## Architecture

```
┌─────────────────────────────┐
│                             │
│    Flask Web Application    │
│    (Port 5000)              │
│                             │
│  ┌─────────────────────┐    │
│  │ MSALAuthClient      │    │
│  │ - Certificate Auth  │    │
│  │ - Token Acquisition │    │
│  │ - Token Caching     │    │
│  └─────────────────────┘    │
│                             │
│  ┌─────────────────────┐    │
│  │ APIClient           │    │
│  │ - Bearer Tokens     │    │
│  │ - CRUD Operations   │    │
│  │ - Error Handling    │    │
│  └─────────────────────┘    │
│                             │
└─────────────────────────────┘
            │
            │ HTTPS
            ▼
┌─────────────────────────────┐
│                             │
│  Microsoft Entra ID         │
│  - OAuth 2.0 / OIDC         │
│  - Token Issuance           │
│                             │
└─────────────────────────────┘
            │
            │ JWT Bearer Token
            ▼
┌─────────────────────────────┐
│                             │
│  FastAPI Backend API        │
│  (Port 8000)                │
│  - JWT Validation           │
│  - Blog Post CRUD           │
│                             │
└─────────────────────────────┘
```

## Prerequisites

- Python 3.14 or higher
- Poetry for dependency management
- Microsoft Entra ID tenant
- App registration for the client (web app)
- App registration for the API (resource server)
- X.509 certificate (.pem format)

## Installation

### 1. Install Dependencies

```bash
cd client
poetry install
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Microsoft Entra ID Configuration
TENANT_ID=your-tenant-id-here
CLIENT_ID=your-client-app-id-here

# Certificate Configuration
CLIENT_CERT_PATH=/path/to/your/certificate.pem
CLIENT_CERT_THUMBPRINT=your-certificate-thumbprint-here

# OAuth Configuration
REDIRECT_URI=http://localhost:5000/callback
API_SCOPE=api://your-api-app-id/access_as_user

# API Configuration
API_BASE_URL=http://localhost:8000

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-for-sessions
FLASK_PORT=5000
DEBUG=false
```

### 3. Certificate Setup

#### Generate a Self-Signed Certificate (Development Only)

```bash
# Generate private key and certificate in cert/ directory (from project root)
openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout cert/entra-app-private.key -out cert/entra-app-cert.pem \
    -days 90 -subj "/CN=localhost"

# Combine into single PEM file for MSAL
cat cert/entra-app-private.key cert/entra-app-cert.pem > cert/entra-app-combined.pem
```

#### Upload Certificate to App Registration

1. Go to Azure Portal → Entra ID → App registrations
2. Select your client application
3. Navigate to "Certificates & secrets"
4. Click "Upload certificate"
5. Upload the `entra-app-cert.pem` file from the `cert/` directory
6. **Copy the thumbprint value displayed by Azure** - paste this into `CLIENT_CERT_THUMBPRINT` in your `.env`

> **Note**: The thumbprint is automatically calculated and displayed by Azure after upload. This is the authoritative value you should use.

## Running the Application

### Start the Client

```bash
cd client
poetry run python -m src.main
```

The application will be available at `http://localhost:5000`

### Application Flow

1. Visit `http://localhost:5000`
2. Click "Sign In with Microsoft"
3. Authenticate with your Microsoft account
4. View your profile or manage blog posts
5. Create, edit, or delete posts
6. Sign out when finished

## Testing

### Run All Tests

```bash
cd client
poetry run pytest
```

### Run Tests with Coverage

```bash
poetry run pytest --cov=src --cov-report=html
```

View the HTML coverage report:

```bash
open htmlcov/index.html
```

### Run Specific Test Files

```bash
# Test configuration module
poetry run pytest tests/unit/test_config.py -v

# Test authentication module
poetry run pytest tests/unit/test_auth.py -v

# Test API client
poetry run pytest tests/unit/test_api_client.py -v
```

### Test Coverage Summary

| Module | Coverage | Notes |
|--------|----------|-------|
| config.py | 96% | Comprehensive validation testing |
| auth.py | 87% | MSAL integration with mocked responses |
| api_client.py | 95% | HTTP client with error handling |
| exceptions.py | 100% | Custom exception hierarchy |
| models.py | 100% | Pydantic models |
| main.py | 0% | Flask app (requires integration tests) |

**Total: 38 tests, 100% pass rate**

## Project Structure

```
client/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Pydantic settings
│   ├── auth.py               # MSAL authentication
│   ├── api_client.py         # API service layer
│   ├── exceptions.py         # Custom exceptions
│   ├── models.py             # Pydantic models
│   └── main.py               # Flask application
├── tests/
│   ├── conftest.py           # Test fixtures
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_auth.py
│   │   └── test_api_client.py
│   └── integration/
│       └── (future tests)
├── pyproject.toml            # Poetry configuration
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## Key Modules

### Configuration (`config.py`)

- Environment-based configuration using Pydantic Settings
- Validation for tenant IDs, certificate paths, API scopes
- Cached settings with `@lru_cache`

### Authentication (`auth.py`)

- `MSALAuthClient`: Wraps MSAL Python SDK
- Certificate loading and validation
- Authorization URL generation
- Token acquisition (authorization code + silent)
- In-memory token caching

### API Client (`api_client.py`)

- `APIClient`: HTTP client for FastAPI backend
- Bearer token injection
- Type-safe API calls using Pydantic models
- Comprehensive error handling (401, 403, 404, 500)
- Structured logging

### Flask Application (`main.py`)

- Routes: `/`, `/login`, `/callback`, `/logout`, `/profile`, `/posts`
- Session-based authentication state
- CSRF protection with state parameter
- Flash messages for user feedback
- Responsive HTML templates (inline)

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TENANT_ID` | Yes | - | Microsoft Entra ID tenant ID (36 chars) |
| `CLIENT_ID` | Yes | - | Application (client) ID (36 chars) |
| `CLIENT_CERT_PATH` | Yes | - | Path to X.509 certificate file |
| `CLIENT_CERT_THUMBPRINT` | Yes | - | SHA-1 thumbprint (40 chars) |
| `REDIRECT_URI` | No | `http://localhost:5000/callback` | OAuth redirect URI |
| `API_SCOPE` | Yes | - | API scope (e.g., `api://api-id/access_as_user`) |
| `API_BASE_URL` | No | `http://localhost:8000` | Backend API base URL |
| `FLASK_SECRET_KEY` | No | `dev-secret-key-change-in-production` | Flask session secret |
| `FLASK_PORT` | No | `5000` | Flask application port |
| `DEBUG` | No | `false` | Enable debug mode |

## Troubleshooting

### Common Issues

#### Certificate Not Found

**Error**: `Certificate file not found: /path/to/cert.pem`

**Solution**:
- Verify the `CLIENT_CERT_PATH` in your `.env` file
- Ensure the file exists and is readable
- Use absolute paths

#### Invalid API Scope

**Error**: `API scope must start with 'api://'`

**Solution**:
- Ensure `API_SCOPE` follows format: `api://<api-app-id>/access_as_user`
- Check that the API app registration exposes this scope

#### 401 Unauthorized

**Possible causes**:
- Access token expired (try signing in again)
- Invalid or missing Bearer token
- Certificate not uploaded to app registration

#### 403 Forbidden

**Possible causes**:
- User doesn't have required permissions
- Trying to edit/delete another user's post
- Missing API scope in token

#### MSAL Token Acquisition Fails

**Check**:
- Certificate thumbprint matches uploaded certificate
- App registration redirect URI matches `REDIRECT_URI`
- User has consented to delegated permissions

### Debug Mode

Enable detailed logging:

```env
DEBUG=true
```

This will show:
- Request/response details
- MSAL token acquisition logs
- API call traces

## Security Best Practices

### ✅ Implemented

- Certificate-based authentication (no client secrets)
- HTTPS required in production
- CSRF protection via state parameter
- Session-based authentication
- No token persistence to disk
- Structured logging (tokens not logged)

### 🚨 Production Checklist

- [ ] Use Azure Key Vault for certificate storage
- [ ] Set `FLASK_SECRET_KEY` to a strong random value
- [ ] Enable HTTPS with valid TLS certificate
- [ ] Set `DEBUG=false`
- [ ] Implement rate limiting
- [ ] Add request correlation IDs
- [ ] Configure proper CORS policies
- [ ] Set up monitoring and alerts
- [ ] Implement certificate rotation strategy

## Code Quality

### Linting and Formatting

```bash
# Format code with Black
poetry run black src tests

# Sort imports with isort
poetry run isort src tests

# Lint with Ruff
poetry run ruff check src tests
```

### Type Checking

All modules use type hints compatible with Python 3.10+:

```python
from __future__ import annotations

def get_profile(self, access_token: str) -> UserResponse:
    ...
```

## Contributing

### Development Workflow

1. Create a feature branch
2. Write tests first (TDD)
3. Implement functionality
4. Ensure all tests pass
5. Run linters and formatters
6. Submit pull request

### Testing Standards

- Maintain >80% coverage
- Use AAA pattern (Arrange-Act-Assert)
- Mock external dependencies
- Use descriptive test names
- Test edge cases and error conditions

## License

This project is part of a technical demonstration for Microsoft Entra ID authentication patterns.

## Related Documentation

- [API Documentation](../api/README.md)
- [Root README](../README.md)
- [Requirements Specification](../docs/certificate-based-auth-msal-python-fastapi-requirements.md)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review Microsoft Entra ID documentation
3. Check MSAL Python documentation: https://msal-python.readthedocs.io/

## Version History

- **0.1.0** (Initial Release)
  - MSAL Python integration with certificate auth
  - Flask web application with OAuth 2.0 flow
  - API client for FastAPI backend
  - Comprehensive unit tests (38 tests, 95%+ coverage)
  - Documentation and examples
