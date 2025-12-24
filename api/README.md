# Blog API

FastAPI downstream API with Microsoft Entra ID authentication using certificate-based MSAL and JWT validation.

## Features

- **Microsoft Entra ID Authentication**: JWT token validation with JWKS
- **Certificate-based Authentication**: Secure authentication without client secrets
- **User and Blog Post CRUD**: Complete REST API for blog management
- **Repository Pattern**: Clean separation of data access logic
- **Service Layer**: Business logic and authorization
- **Comprehensive Testing**: Unit and integration tests with >80% coverage
- **Type Safety**: Full type hints and Pydantic validation
- **Production Ready**: Structured logging, error handling, and configuration management

## Architecture

```
api/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── auth.py              # JWT validation and authentication
│   ├── models.py            # SQLModel database models and Pydantic schemas
│   ├── database.py          # Database connection and session management
│   ├── repositories.py      # Repository pattern for data access
│   ├── services.py          # Business logic layer
│   ├── routes.py            # API endpoint handlers
│   └── exceptions.py        # Custom exception classes
├── tests/
│   ├── conftest.py          # Pytest fixtures and configuration
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── pyproject.toml           # Poetry dependencies and configuration
└── README.md
```

## Prerequisites

- Python 3.10+ (tested on Python 3.10, 3.11, 3.12, 3.13, 3.14)
- Poetry for dependency management
- Microsoft Entra ID tenant with configured app registrations

## Setup

### 1. Install Dependencies

```bash
cd api
poetry install
```

### 2. Configure Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Update the following required variables:

```env
TENANT_ID=your-tenant-id-here
API_APP_ID_URI=api://your-api-client-id
REQUIRED_SCOPE=access_as_user
DATABASE_URL=sqlite:///./blog_api.db
```

### 3. Azure App Registration Setup

#### API Application (Resource Server)

1. Register a new application in Microsoft Entra Admin Center
2. **Expose an API**:
   - Set Application ID URI: `api://<client-id>`
   - Add scope: `access_as_user`
3. **Optional**: Add App Roles for fine-grained permissions
4. Copy the **Client ID** and **Tenant ID**

## Running the API

### Development Mode

```bash
poetry run python -m src.main
```

Or using uvicorn directly:

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/v1/docs
- ReDoc: http://localhost:8000/v1/redoc

### Seed Sample Data

For local development and testing, populate the database with sample data:

```bash
# Default: 3 users and 20 blog posts
poetry run python scripts/seed_data.py

# Clear existing data and create 5 users with 50 posts
poetry run python scripts/seed_data.py --clear --users 5 --count 50

# View all options
poetry run python scripts/seed_data.py --help
```

**Options:**
- `--clear`: Clear all existing data before seeding
- `--users N`: Number of users to create (default: 3)
- `--count N`: Number of blog posts to create (default: 20)

## API Endpoints

### Authentication

All endpoints (except `/health`) require a valid JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (no auth required) |
| GET | `/v1/profile` | Get current user profile from token |
| POST | `/v1/users/me` | Register/retrieve current user |
| POST | `/v1/posts` | Create a blog post |
| GET | `/v1/posts` | List all blog posts (paginated) |
| GET | `/v1/posts/{id}` | Get specific blog post |
| PUT | `/v1/posts/{id}` | Update blog post (owner only) |
| DELETE | `/v1/posts/{id}` | Delete blog post (owner only) |

### Example Request

```bash
curl -X POST http://localhost:8000/v1/posts \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "This is the content of my post."
  }'
```

## Testing

### Run All Tests

```bash
poetry run pytest
```

### Run with Coverage

```bash
poetry run pytest --cov=src --cov-report=html --cov-report=term-missing
```

### Run Specific Test Suite

```bash
# Unit tests only
poetry run pytest tests/unit/

# Integration tests only
poetry run pytest tests/integration/

# Specific test file
poetry run pytest tests/unit/test_services.py
```

### View Coverage Report

```bash
open htmlcov/index.html
```

## Code Quality

### Linting

```bash
poetry run ruff check src/ tests/
```

### Formatting

```bash
poetry run black src/ tests/
poetry run isort src/ tests/
```

### Type Checking

```bash
poetry run mypy src/
```

## JWT Token Validation

The API validates JWT tokens from Microsoft Entra ID:

1. **Signature Verification**: RS256 using JWKS from Microsoft
2. **Issuer Validation**: Ensures token issued by correct tenant
3. **Audience Validation**: Verifies token intended for this API
4. **Expiration Check**: Rejects expired tokens
5. **Scope Validation**: Requires `access_as_user` scope

## Authorization

### Ownership Validation

Blog post update and delete operations enforce ownership:
- Only the author (matched by `oid` from token) can modify their posts
- Attempting to modify another user's post returns `403 Forbidden`

### User Management

- Users are automatically created/retrieved based on token `oid`
- User display name is extracted from token `name` claim

## Database

### SQLite (Development)

Default configuration uses SQLite for local development:

```env
DATABASE_URL=sqlite:///./blog_api.db
```

### PostgreSQL/Azure SQL (Production)

For production, update the connection string:

```env
DATABASE_URL=postgresql://user:password@host:port/database
```

### Migrations

Database tables are automatically created on application startup. For production, consider using Alembic for migrations.

## Deployment

### Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-dev

COPY src/ ./src/

CMD ["python", "-m", "src.main"]
```

Build and run:

```bash
docker build -t blog-api .
docker run -p 8000:8000 --env-file .env blog-api
```

### Azure App Service

1. Configure environment variables in Application Settings
2. Deploy using Azure CLI or GitHub Actions
3. Use Azure Key Vault for sensitive configuration

## Troubleshooting

### 401 Unauthorized

- Verify token is valid and not expired
- Check `aud` claim matches `API_APP_ID_URI`
- Ensure token has required scope `access_as_user`
- Verify `TENANT_ID` is correct

### 403 Forbidden

- User lacks permission to access resource
- For blog posts, verify user is the author

### Database Errors

- Ensure `DATABASE_URL` is correctly configured
- Check file permissions for SQLite database
- Verify database server is accessible for remote databases

## Contributing

1. Follow the established architecture patterns
2. Write tests for all new features (maintain >80% coverage)
3. Use type hints and docstrings
4. Run linting and formatting before committing
5. Update documentation for API changes

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:

- Review the [requirements document](../docs/certificate-based-auth-msal-python-fastapi-requirements.md)
- Check the interactive API documentation at `/v1/docs`
- Review Microsoft Entra ID documentation for authentication issues
