
# Technical Requirements Specification

**MSAL Python Client with Certificate Authentication and FastAPI Downstream API (Poetry‑managed)**

***

## 1. Purpose and Scope

This document defines the **technical requirements** for a production-ready Python solution that:

*   Authenticates users using the **Microsoft identity platform (Microsoft Entra ID)**
*   Uses **MSAL for Python** with **certificate-based authentication**
*   Acquires user-delegated access tokens via **OAuth 2.0 Authorization Code Flow with OpenID Connect**
*   Calls a protected **downstream REST API** implemented using **FastAPI**
*   Manages dependencies using **Poetry**
*   Implements a **User and Blog Post CRUD API** as a reference workload
*   Follows **secure-by-default** and **cloud-ready** practices

The solution is intended for:

*   Technical documentation
*   Developer samples
*   Customer reference architectures
*   Production-quality starter projects

***

## 2. Non-Goals

The following are explicitly out of scope:

*   Legacy Azure AD Authentication Library (ADAL)
*   Client secrets in production environments
*   Implicit grant or ROPC flows
*   Monolithic backend architecture
*   Custom identity providers outside Microsoft Entra ID

***

## 3. High-Level Architecture

### 3.1 Repository Structure

The solution **MUST** use a **monorepo** structure with independent Poetry projects:

    repo-root/
    ├── client/           # Python client application
    │   ├── pyproject.toml
    │   ├── poetry.lock
    │   └── src/
    ├── api/              # FastAPI downstream API
    │   ├── pyproject.toml
    │   ├── poetry.lock
    │   └── src/
    ├── docs/
    └── README.md

This structure keeps dependency graphs isolated and versioned cleanly while maintaining both components in the same repository.

### 3.2 Logical Components

    +-------------------+        +---------------------------+
    |                   |        |                           |
    |  Python Client    |        |   FastAPI Downstream API  |
    |  (Flask/FastAPI)  | -----> |   (Microservice)          |
    |                   |        |                           |
    | MSAL (Cert Auth)  |        | JWT Validation (JWKS)     |
    | Authorization     |        | User & Blog CRUD          |
    | Code Flow (OIDC)  |        |                           |
    +-------------------+        +---------------------------+
                |
                v
    +-------------------------------------------------------+
    |                   Microsoft Entra ID                  |
    |   OAuth 2.0 / OpenID Connect / Token Issuance          |
    +-------------------------------------------------------+

***

## 4. Identity and Authentication Requirements

### 4.1 Identity Provider

*   The solution **MUST** use **Microsoft Entra ID**
*   The solution **MUST NOT** implement a custom authentication mechanism

### 4.2 Application Registrations

#### 4.2.1 Client Application (Web App)

| Requirement       | Value                                |
| ----------------- | ------------------------------------ |
| Platform          | Web                                  |
| Auth Flow         | Authorization Code Flow with PKCE    |
| Token Acquisition | MSAL Python                          |
| Credential Type   | **Certificate-based authentication** |
| Account Types     | Single-tenant (default)              |
| Secrets           | **NOT allowed for production**       |

#### 4.2.2 API Application (Resource Server)

| Requirement        | Value                                      |
| ------------------ | ------------------------------------------ |
| Expose API         | Required                                   |
| Application ID URI | `api://<api-client-id>`                    |
| Scopes             | `access_as_user`                           |
| Optional App Roles | `Blog.Reader`, `Blog.Writer`, `Blog.Admin` |

***

## 5. Cryptography and Certificate Requirements

### 5.1 Certificate Usage

*   Client authentication **MUST** use X.509 certificates
*   Certificates **MUST** be uploaded to the client app registration
*   Certificates **MUST NOT** be committed to source control

### 5.2 Key Management

| Environment | Requirement              |
| ----------- | ------------------------ |
| Local Dev   | Local PEM or PFX file    |
| Production  | Azure Key Vault          |
| Rotation    | Supported and documented |

***

## 6. Dependency Management (Poetry)

### 6.1 General Rules

*   All Python projects **MUST** use Poetry
*   The solution **MUST** use a **monorepo** structure
*   Both `client/` and `api/` **MUST** be independent Poetry projects
*   Each service **MUST** have its own `pyproject.toml` and `poetry.lock`
*   Lock files **MUST** be committed
*   Dependency graphs **MUST** remain isolated between client and API

### 6.2 Client Dependencies

Required packages:

*   `msal`
*   `flask` or `fastapi`
*   `requests`
*   `python-dotenv`

Development dependencies:

*   `pytest`
*   `pytest-cov`
*   `pytest-asyncio`
*   `pytest-mock`
*   `httpx` (for testing)

### 6.3 API Dependencies

Required packages:

*   `fastapi`
*   `uvicorn`
*   `python-jose`
*   `httpx`
*   `sqlmodel`
*   `pydantic`

Development dependencies:

*   `pytest`
*   `pytest-cov`
*   `pytest-asyncio`
*   `httpx` (for TestClient)
*   `faker` (for test data generation)

***

## 7. OAuth 2.0 and Token Flow Requirements

### 7.1 Authorization Code Flow

The client **MUST**:

1.  Redirect user to Microsoft identity platform authorization endpoint
2.  Request delegated API scope (`access_as_user`)
3.  Receive authorization code
4.  Exchange authorization code for access token using MSAL
5.  Cache token securely in memory/session

### 7.2 Token Usage

*   Access tokens **MUST** be sent as `Authorization: Bearer <token>`
*   ID tokens **MUST NOT** be used for API access

***

## 8. Downstream API Security Requirements

### 8.1 JWT Validation

The API **MUST** validate:

| Claim            | Requirement                       |
| ---------------- | --------------------------------- |
| issuer (`iss`)   | Must match tenant v2.0 endpoint   |
| audience (`aud`) | Must equal API Application ID URI |
| signature        | RS256 via JWKS                    |
| expiry (`exp`)   | Enforced                          |
| scope (`scp`)    | `access_as_user` OR valid role    |

### 8.2 Authorization Model

*   Delegated permissions via scopes
*   Optional authorization via app roles
*   Ownership checks optional but recommended

***

## 9. API Functional Requirements (CRUD)

### 9.1 User Model

| Field         | Description               |
| ------------- | ------------------------- |
| id            | Internal DB ID            |
| oid           | Microsoft Entra object ID |
| display\_name | Optional                  |

### 9.2 Blog Post Model

| Field      | Description         |
| ---------- | ------------------- |
| id         | Primary key         |
| title      | Required            |
| content    | Required            |
| author\_id | Foreign key to User |

### 9.3 API Endpoints

#### Identity

*   `GET /v1/profile`

#### User

*   `POST /v1/users/me`

#### Blog Posts

*   `POST /v1/posts`
*   `GET /v1/posts`
*   `GET /v1/posts/{id}`
*   `PUT /v1/posts/{id}`
*   `DELETE /v1/posts/{id}`

All endpoints **MUST** require a valid access token.

***

## 10. Data Storage Requirements

*   SQL-based persistence layer
*   SQLite allowed for development
*   Azure SQL / PostgreSQL recommended for production
*   ORM: SQLModel or SQLAlchemy

***

## 11. Testing and Code Quality Requirements

### 11.1 Testing Framework

*   Both `client/` and `api/` **MUST** use **pytest** as the testing framework
*   Tests **MUST** be organized in `tests/` directories at the project level
*   Test coverage **MUST** be ≥ 80% for core business logic

### 11.2 Test Structure (Senior Engineering Standards)

Each project **MUST** include:

#### Unit Tests
*   Isolated component testing with mocked dependencies
*   Parametrized tests using `@pytest.mark.parametrize`
*   Fixtures for reusable test data and setup
*   Proper use of `pytest.fixture` with appropriate scopes

#### Integration Tests
*   End-to-end API flow testing
*   JWT token validation testing
*   Database integration tests with test databases
*   MSAL authentication flow mocking

#### Test Organization
```
client/tests/
├── conftest.py          # Shared fixtures
├── unit/
│   ├── test_auth.py     # MSAL wrapper tests
│   └── test_utils.py
└── integration/
    └── test_api_calls.py

api/tests/
├── conftest.py
├── unit/
│   ├── test_jwt_validation.py
│   ├── test_models.py
│   └── test_services.py
└── integration/
    └── test_endpoints.py
```

### 11.3 Testing Best Practices

**MUST** demonstrate:

*   **Dependency Injection**: Testable architecture with injected dependencies
*   **Mocking**: Use `pytest-mock` or `unittest.mock` for external services
*   **Test Isolation**: Each test runs independently without shared state
*   **AAA Pattern**: Arrange-Act-Assert structure in all tests
*   **Descriptive Names**: Test functions clearly describe what is being tested
*   **Edge Cases**: Test boundary conditions, errors, and exception handling

### 11.4 Required Test Scenarios

#### Client Tests
*   MSAL token acquisition (mocked)
*   Certificate loading and validation
*   Token caching behavior
*   Error handling for failed authentication
*   API request construction with Bearer tokens

#### API Tests
*   JWT signature validation
*   JWT expiration handling
*   Missing/malformed token responses (401)
*   Insufficient permissions (403)
*   CRUD operations with valid tokens
*   Ownership validation logic
*   Database transactions and rollbacks

### 11.5 Code Coverage

*   Use `pytest-cov` for coverage reporting
*   Generate HTML coverage reports
*   Exclude test files and configuration from coverage metrics
*   CI/CD pipeline **MUST** fail if coverage drops below 80%

### 11.6 Code Quality Standards

**MUST** include:

*   Type hints throughout the codebase (Python 3.10+)
*   Docstrings for all public functions and classes
*   Linting with `ruff` or `flake8`
*   Code formatting with `black`
*   Import sorting with `isort`
*   Pre-commit hooks for automated quality checks

### 11.7 Senior Engineering Patterns

The codebase **MUST** demonstrate:

*   **Repository Pattern**: Abstract data access layer
*   **Service Layer**: Business logic separated from API routes
*   **Dependency Injection**: Constructor or FastAPI Depends()
*   **Error Handling**: Custom exceptions with proper HTTP status codes
*   **Logging**: Structured logging with context
*   **Configuration Management**: Environment-based configuration
*   **Async/Await**: Proper async patterns where applicable

***

## 12. Configuration and Environment Variables

Required environment variables:

### Client

    TENANT_ID
    CLIENT_ID
    CLIENT_CERT_PATH
    CLIENT_CERT_THUMBPRINT
    REDIRECT_URI
    API_SCOPE
    API_BASE_URL

### API

    TENANT_ID
    API_APP_ID_URI
    REQUIRED_SCOPE
    DATABASE_URL

***

## 13. Observability and Diagnostics

*   Structured application logging
*   Correlation ID propagation
*   Application Insights / OpenTelemetry recommended
*   Access tokens **MUST NOT** be logged

***

## 14. Deployment Requirements

### 14.1 Supported Deployment Targets

*   Azure App Service
*   Azure Container Apps
*   Docker-based CI/CD

### 14.2 CI/CD

*   Federated credentials **REQUIRED**
*   No secrets in pipelines
*   Infrastructure as code (Bicep or Terraform)
*   Automated testing in CI pipeline
*   Coverage reporting and quality gates

***

## 15. Security and Compliance Requirements

*   HTTPS only
*   TLS 1.2+
*   Principle of least privilege
*   No token persistence to disk
*   GDPR-compliant logging and data handling

***

## 16. Documentation Requirements

The final project **MUST** include:

*   Root-level README with monorepo overview and setup instructions
*   Individual READMEs for `client/` and `api/` directories
*   Architecture diagram showing monorepo structure
*   App registration screenshots
*   Common error troubleshooting (401/403)
*   Local vs production differences
*   Guidance on running client and API independently or together
*   Testing guide with instructions to run tests and generate coverage reports
*   Code quality standards and contribution guidelines

***

## 17. Success Criteria

The solution is considered complete when:

*   A user can sign in with Microsoft Entra ID
*   The client acquires an access token using a certificate
*   The client successfully calls the FastAPI downstream API
*   CRUD operations function with enforced authorization
*   The solution runs locally and is cloud-deployment ready
*   All tests pass with ≥80% code coverage
*   Code demonstrates senior engineering practices and patterns
*   Linting and formatting checks pass
*   Documentation is comprehensive and professionally written

***
