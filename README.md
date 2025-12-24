# MSAL Python Certificate Authentication with FastAPI

A production-ready monorepo demonstrating **Microsoft Entra ID** authentication using **MSAL Python** with **X.509 certificate-based authentication** and a protected **FastAPI** backend API.

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         MONOREPO                                 │
│                                                                  │
│  ┌────────────────────────┐     ┌───────────────────────────┐   │
│  │                        │     │                           │   │
│  │   Client (Flask)       │     │   API (FastAPI)           │   │
│  │   Port: 5000           │────▶│   Port: 8000              │   │
│  │                        │     │                           │   │
│  │  • MSAL Auth (Cert)    │     │  • JWT Validation         │   │
│  │  • OAuth 2.0 Flow      │     │  • JWKS (RS256)           │   │
│  │  • Token Management    │     │  • Blog CRUD API          │   │
│  │  • Web UI              │     │  • SQLModel + SQLite      │   │
│  │                        │     │                           │   │
│  │  38 Unit Tests         │     │  69 Unit Tests            │   │
│  │  95%+ Coverage         │     │  86% Coverage             │   │
│  │                        │     │                           │   │
│  └────────────────────────┘     └───────────────────────────┘   │
│             │                              ▲                     │
│             │                              │                     │
└─────────────┼──────────────────────────────┼─────────────────────┘
              │                              │
              │ HTTPS                        │ JWT Bearer Token
              ▼                              │
    ┌─────────────────────────────────────────────────┐
    │                                                 │
    │         Microsoft Entra ID                      │
    │                                                 │
    │  • OAuth 2.0 Authorization Server               │
    │  • OpenID Connect Provider                      │
    │  • Token Issuance (Access + ID tokens)          │
    │  • JWKS Endpoint (Public Keys for JWT)          │
    │                                                 │
    └─────────────────────────────────────────────────┘
```

## ✨ Key Features

### 🔐 Security First
- **Certificate-Based Authentication**: No client secrets in production
- **OAuth 2.0 Authorization Code Flow**: Industry-standard secure authentication
- **JWT Validation**: RS256 signature verification with JWKS
- **User Delegation**: Access tokens represent authenticated users

### 🎯 Production Ready
- **Monorepo Structure**: Independent Poetry projects for client and API
- **Comprehensive Testing**: 107 total tests with >80% coverage
- **Senior Engineering Patterns**: Repository pattern, service layer, dependency injection
- **Type Safety**: Full Python type hints (Python 3.14)
- **Error Handling**: Custom exceptions with proper HTTP status codes

### 📝 Complete Implementation
- **Client Application**: Flask web app with MSAL authentication
- **API Application**: FastAPI with JWT validation and CRUD operations
- **Database**: SQLModel ORM with SQLite (PostgreSQL/Azure SQL ready)
- **Documentation**: Comprehensive guides for setup and deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.14 or higher
- Poetry (dependency management)
- Microsoft Entra ID tenant
- Two app registrations (client + API)
- X.509 certificate

### 1. Clone Repository

```bash
git clone <repository-url>
cd msal-python-cert-auth-fastapi-api
```

### 2. Set Up API

```bash
cd api
poetry install
cp .env.example .env
# Edit .env with your API configuration
poetry run pytest  # Run tests
poetry run python -m src.main  # Start API on port 8000
```

### 3. Set Up Client

```bash
cd ../client
poetry install
cp .env.example .env
# Edit .env with your client configuration
poetry run pytest  # Run tests
poetry run python -m src.main  # Start client on port 5000
```

### 4. Test the Application

1. Visit `http://localhost:5000`
2. Click "Sign In with Microsoft"
3. Authenticate with your Entra ID account
4. Create and manage blog posts
5. Sign out

## 📁 Repository Structure

```
msal-python-cert-auth-fastapi-api/
├── README.md                    # This file
├── docs/
│   └── certificate-based-auth-msal-python-fastapi-requirements.md
│
├── client/                      # Flask client application
│   ├── README.md                # Client documentation
│   ├── pyproject.toml           # Poetry dependencies
│   ├── poetry.lock              # Locked dependencies
│   ├── .env.example             # Environment template
│   ├── src/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic settings
│   │   ├── auth.py              # MSAL authentication
│   │   ├── api_client.py        # API service layer
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── models.py            # Pydantic models
│   │   └── main.py              # Flask application
│   └── tests/
│       ├── conftest.py          # Test fixtures
│       ├── unit/
│       │   ├── test_config.py
│       │   ├── test_auth.py
│       │   └── test_api_client.py
│       └── integration/         # (Future)
│
└── api/                         # FastAPI backend API
    ├── README.md                # API documentation
    ├── pyproject.toml           # Poetry dependencies
    ├── poetry.lock              # Locked dependencies
    ├── .env.example             # Environment template
    ├── src/
    │   ├── __init__.py
    │   ├── config.py            # Pydantic settings
    │   ├── database.py          # Database session
    │   ├── models.py            # SQLModel models
    │   ├── repositories.py      # Data access layer
    │   ├── services.py          # Business logic
    │   ├── routes.py            # API endpoints
    │   ├── auth.py              # JWT validation
    │   ├── exceptions.py        # Custom exceptions
    │   └── main.py              # FastAPI application
    ├── tests/
    │   ├── conftest.py          # Test fixtures
    │   ├── unit/                # 69 unit tests
    │   └── integration/         # Integration tests
    └── scripts/
        ├── seed_data.py         # Database seeder
        └── README.md            # Seeder documentation
```

## 🔧 Microsoft Entra ID Configuration

### App Registration 1: Client Application

1. **Create App Registration**
   - Name: `Blog Client`
   - Account types: Single-tenant (default)
   - Redirect URI: `http://localhost:5000/callback` (Web platform)

2. **Upload Certificate**
   - Navigate to "Certificates & secrets"
   - Upload the `cert/entra-app-cert.pem` file
   - **Copy the thumbprint value displayed by Azure** and save it for `CLIENT_CERT_THUMBPRINT`

3. **Configure API Permissions**
   - Add delegated permission from API app: `access_as_user`
   - Grant admin consent

4. **Note Configuration Values**
   - Application (client) ID
   - Directory (tenant) ID

### App Registration 2: API Application

1. **Create App Registration**
   - Name: `Blog API`
   - Account types: Single-tenant (default)
   - No redirect URI needed

2. **Expose API**
   - Application ID URI: `api://<api-client-id>`
   - Add scope: `access_as_user`
     - Who can consent: Admins and users
     - Display name: "Access blog API as user"
     - Description: "Allows the app to access the blog API on your behalf"

3. **Note Configuration Values**
   - Application (client) ID
   - Application ID URI

## 🔐 Certificate Setup

### Generate Self-Signed Certificate (Development)

```bash
# Generate private key and certificate in cert/ directory
openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout cert/entra-app-private.key -out cert/entra-app-cert.pem \
    -days 90 -subj "/CN=localhost"

# Combine into single PEM file for MSAL
cat cert/entra-app-private.key cert/entra-app-cert.pem > cert/entra-app-combined.pem
```

### Production Certificate

For production, use:

- Azure Key Vault for certificate storage
- Managed Identity for certificate access
- Certificate Authority (CA) signed certificates
- Automated certificate rotation

## 🧪 Testing

### Run All Tests

```bash
# API tests
cd api
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html

# Client tests
cd ../client
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Test Summary

| Project | Tests | Pass Rate | Coverage | Key Modules |
|---------|-------|-----------|----------|-------------|
| **API** | 69 | 100% | 86% | config (100%), models (100%), services (100%) |
| **Client** | 38 | 100% | 95%+ | config (96%), api_client (95%), auth (87%) |
| **Total** | **107** | **100%** | **~90%** | Comprehensive unit testing |

## 🗄️ Database Management

### Seed Sample Data (API)

```bash
cd api

# Default: 3 users, 20 posts
poetry run python scripts/seed_data.py

# Clear existing data and create custom dataset
poetry run python scripts/seed_data.py --clear --users 5 --count 50

# Get help
poetry run python scripts/seed_data.py --help
```

### Database Schema

**Users Table:**

- id (Integer, Primary Key)
- oid (String, Unique) - Microsoft Entra ID object ID
- display_name (String, Nullable)
- created_at (DateTime, UTC)
- updated_at (DateTime, UTC)

**BlogPosts Table:**

- id (Integer, Primary Key)
- title (String, 200 chars max)
- content (Text)
- author_id (Integer, Foreign Key → Users)
- created_at (DateTime, UTC)
- updated_at (DateTime, UTC)

## 🔑 Environment Variables

### Client (.env)

```env
TENANT_ID=your-tenant-id
CLIENT_ID=your-client-app-id
CLIENT_CERT_PATH=/path/to/client_cert.pem
CLIENT_CERT_THUMBPRINT=your-cert-thumbprint
REDIRECT_URI=http://localhost:5000/callback
API_SCOPE=api://your-api-app-id/access_as_user
API_BASE_URL=http://localhost:8000
FLASK_SECRET_KEY=generate-strong-random-key
FLASK_PORT=5000
DEBUG=false
```

### API (.env)

```env
TENANT_ID=your-tenant-id
API_APP_ID_URI=api://your-api-app-id
REQUIRED_SCOPE=access_as_user
DATABASE_URL=sqlite:///./blog_api.db
```

## 📚 API Endpoints

### Authentication

- `GET /v1/profile` - Get current user profile (creates user if not exists)

### Blog Posts

- `POST /v1/posts` - Create new blog post
- `GET /v1/posts` - List all blog posts (paginated)
- `GET /v1/posts/{id}` - Get single blog post
- `PUT /v1/posts/{id}` - Update blog post (author only)
- `DELETE /v1/posts/{id}` - Delete blog post (author only)

All endpoints require valid JWT Bearer token in `Authorization` header.

## 🎨 Client Routes

- `/` - Home page (public)
- `/login` - Initiate OAuth flow
- `/callback` - OAuth callback handler
- `/logout` - Sign out
- `/profile` - View user profile (protected)
- `/posts` - List blog posts (protected)
- `/posts/<id>` - View single post (protected)
- `/posts/new` - Create post form (protected)
- `/posts/<id>/edit` - Edit post form (protected, author only)
- `/posts/<id>/delete` - Delete post (protected, author only)

## 🛠️ Development Workflow

### Code Quality Tools

```bash
# Format code
poetry run black src tests
poetry run isort src tests

# Lint code
poetry run ruff check src tests

# Run tests with coverage
poetry run pytest --cov=src --cov-report=term-missing
```

### Monorepo Management

Each project (`client/` and `api/`) is an independent Poetry project:

- Separate dependency graphs
- Independent versioning
- Isolated virtual environments
- Can be deployed independently

## 🚀 Deployment

### Local Development

```bash
# Terminal 1: Start API
cd api && poetry run python -m src.main

# Terminal 2: Start Client
cd client && poetry run python -m src.main
```

### Production Deployment

Recommended platforms:

- **Azure App Service** (Web Apps)
- **Azure Container Apps**
- **Docker + Kubernetes (AKS)**
- **AWS ECS/Fargate**

Key considerations:

- Use Azure Key Vault for certificates
- Enable HTTPS only (TLS 1.2+)
- Configure managed identity
- Set up Application Insights
- Implement health checks
- Configure auto-scaling

## 🔒 Security Best Practices

### ✅ Implemented

- Certificate-based authentication (no secrets)
- JWT signature validation (RS256 with JWKS)
- CSRF protection (state parameter)
- Input validation (Pydantic)
- SQL injection prevention (SQLModel/SQLAlchemy)
- Proper error handling (no sensitive data leakage)
- Structured logging (no token logging)

### 🚨 Production Checklist

- [ ] Azure Key Vault for certificate storage
- [ ] Managed Identity for certificate access
- [ ] HTTPS with valid TLS certificate
- [ ] Secret rotation strategy
- [ ] Rate limiting
- [ ] CORS configuration
- [ ] Request correlation IDs
- [ ] Monitoring and alerting
- [ ] Security headers (HSTS, CSP, etc.)
- [ ] Vulnerability scanning

## 📖 Documentation

- [Client README](client/README.md) - Detailed client setup and usage
- [API README](api/README.md) - Detailed API setup and usage
- [Requirements Specification](docs/certificate-based-auth-msal-python-fastapi-requirements.md) - Technical requirements
- [Database Seeder](api/scripts/README.md) - Data seeding guide

## 🐛 Troubleshooting

### Common Issues

#### 401 Unauthorized from API

**Causes:**

- Invalid or expired access token
- Wrong `aud` (audience) claim
- Missing or invalid `scp` (scope) claim

**Solutions:**

- Check token expiration (default: 1 hour)
- Verify API_APP_ID_URI matches token audience
- Ensure access_as_user scope is granted

#### 403 Forbidden

**Causes:**

- User trying to modify another user's post
- Missing required permissions

**Solutions:**

- Verify user is post author
- Check delegated permissions in app registration

#### Certificate Errors

**Causes:**

- Certificate not uploaded to app registration
- Thumbprint mismatch
- Certificate expired

**Solutions:**

- Re-upload certificate to Azure Portal
- Verify thumbprint matches (case-insensitive, no colons)
- Generate new certificate if expired

## 🤝 Contributing

This is a technical demonstration project. For production use:

1. Follow security best practices
2. Implement additional error handling
3. Add comprehensive logging
4. Set up monitoring
5. Configure CI/CD pipelines
6. Add integration tests
7. Implement database migrations
8. Add API rate limiting

## 📄 License

This project is a technical demonstration for Microsoft Entra ID authentication patterns.

## 🙏 Acknowledgments

- Microsoft Identity Platform
- MSAL Python library
- FastAPI framework
- SQLModel library
- Flask framework

## 📞 Support

For issues:

1. Check troubleshooting sections in README files
2. Review Microsoft Entra ID documentation
3. Check MSAL Python documentation
4. Review FastAPI documentation

## Version

**Current Version**: 1.0.0

### Changelog

**v1.0.0** - Initial Release

- ✅ MSAL Python with certificate authentication
- ✅ Flask client with OAuth 2.0 Authorization Code Flow
- ✅ FastAPI backend with JWT validation
- ✅ SQLModel ORM with User and BlogPost models
- ✅ Repository pattern and service layer
- ✅ 107 comprehensive unit tests (100% pass rate)
- ✅ 86-95% test coverage
- ✅ Database seeding utility
- ✅ Complete documentation
- ✅ Production-ready error handling
- ✅ Monorepo structure with Poetry
