# API Documentation

## Overview

The Blog API is a production-ready RESTful API built with FastAPI, implementing Microsoft Entra ID authentication with certificate-based MSAL Python. It demonstrates senior software engineering practices including layered architecture, comprehensive testing, security best practices, and enterprise-grade observability.

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────┐
│         API Layer (Routes)          │
│  - HTTP handling                    │
│  - Request/response formatting      │
│  - Authentication enforcement       │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│      Service Layer (Business)       │
│  - Business logic                   │
│  - Authorization rules              │
│  - Transaction coordination         │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│    Repository Layer (Data Access)   │
│  - Database operations              │
│  - Query construction               │
│  - Data mapping                     │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│         Database (SQLModel)         │
│  - Data persistence                 │
│  - Relationship management          │
└─────────────────────────────────────┘
```

### Key Components

#### Middleware Stack
1. **RateLimitMiddleware**: Token bucket rate limiting
2. **SecurityHeadersMiddleware**: Security headers (HSTS, CSP, etc.)
3. **RequestLoggingMiddleware**: Structured request/response logging
4. **CorrelationIdMiddleware**: Distributed tracing support
5. **CORSMiddleware**: Cross-origin resource sharing

#### Authentication Flow
```
Client Request → Bearer Token → JWT Validation → JWKS Signature Check
                                                        ↓
                                                  Claims Extraction
                                                        ↓
                                                  Scope Validation
                                                        ↓
                                                  Route Handler
```

## API Endpoints

### Health Check Endpoints

#### `GET /health`
Simple health check (backward compatible)

**Response:**
```json
{
  "status": "healthy",
  "version": "v1"
}
```

#### `GET /health`
Detailed health check with component status

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-24T12:00:00Z",
  "version": "v1",
  "environment": "production",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database is accessible"
    },
    "jwks": {
      "status": "healthy",
      "message": "JWKS endpoint is accessible",
      "response_time_ms": 45.2
    }
  }
}
```

#### `GET /health/live`
Kubernetes liveness probe

**Response:**
```json
{
  "status": "alive"
}
```

#### `GET /health/ready`
Kubernetes readiness probe

**Response:**
```json
{
  "status": "ready"
}
```

### Authentication Endpoints

#### `GET /v1/profile`
Get current user profile from token claims

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "oid": "user-object-id",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "preferred_username": "john@example.com"
}
```

**Errors:**
- `401 Unauthorized`: Invalid or missing token

### User Endpoints

#### `POST /v1/users/me`
Register or retrieve current user

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "id": 1,
  "oid": "user-object-id",
  "display_name": "John Doe",
  "created_at": "2024-12-24T12:00:00Z",
  "updated_at": "2024-12-24T12:00:00Z"
}
```

### Blog Post Endpoints

#### `POST /v1/posts`
Create a new blog post

**Headers:**
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "title": "My Blog Post",
  "content": "This is the content of my blog post."
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "title": "My Blog Post",
  "content": "This is the content of my blog post.",
  "author_id": 1,
  "created_at": "2024-12-24T12:00:00Z",
  "updated_at": "2024-12-24T12:00:00Z"
}
```

**Errors:**
- `401 Unauthorized`: Invalid or missing token
- `422 Unprocessable Entity`: Invalid input data

#### `GET /v1/posts`
List all blog posts (paginated)

**Headers:**
- `Authorization: Bearer <access_token>`

**Query Parameters:**
- `skip` (integer, default: 0): Number of posts to skip
- `limit` (integer, default: 100, max: 1000): Maximum posts to return

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "Blog Post 1",
    "content": "Content of post 1",
    "author_id": 1,
    "created_at": "2024-12-24T12:00:00Z",
    "updated_at": "2024-12-24T12:00:00Z",
    "author": {
      "id": 1,
      "oid": "user-object-id",
      "display_name": "John Doe",
      "created_at": "2024-12-24T12:00:00Z",
      "updated_at": "2024-12-24T12:00:00Z"
    }
  }
]
```

#### `GET /v1/posts/{id}`
Get a specific blog post

**Headers:**
- `Authorization: Bearer <access_token>`

**Path Parameters:**
- `id` (integer): Post ID

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Blog Post 1",
  "content": "Content of post 1",
  "author_id": 1,
  "created_at": "2024-12-24T12:00:00Z",
  "updated_at": "2024-12-24T12:00:00Z",
  "author": {
    "id": 1,
    "oid": "user-object-id",
    "display_name": "John Doe",
    "created_at": "2024-12-24T12:00:00Z",
    "updated_at": "2024-12-24T12:00:00Z"
  }
}
```

**Errors:**
- `404 Not Found`: Post does not exist

#### `PUT /v1/posts/{id}`
Update a blog post (author only)

**Headers:**
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters:**
- `id` (integer): Post ID

**Request Body:**
```json
{
  "title": "Updated Title",
  "content": "Updated content"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Updated Title",
  "content": "Updated content",
  "author_id": 1,
  "created_at": "2024-12-24T12:00:00Z",
  "updated_at": "2024-12-24T12:30:00Z"
}
```

**Errors:**
- `403 Forbidden`: User is not the post author
- `404 Not Found`: Post does not exist

#### `DELETE /v1/posts/{id}`
Delete a blog post (author only)

**Headers:**
- `Authorization: Bearer <access_token>`

**Path Parameters:**
- `id` (integer): Post ID

**Response:** `204 No Content`

**Errors:**
- `403 Forbidden`: User is not the post author
- `404 Not Found`: Post does not exist

## Error Responses

All errors follow a consistent format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "status_code": 400,
  "timestamp": "2024-12-24T12:00:00Z",
  "path": "/v1/posts",
  "correlation_id": "abc-123-def",
  "errors": [
    {
      "code": "VALUE_ERROR",
      "message": "Title must be between 1 and 200 characters",
      "field": "title"
    }
  ]
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request format
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource does not exist
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

API implements token bucket rate limiting:

### Rate Limits by Endpoint Type

- **Authentication**: 10 requests/minute
- **Write Operations** (POST, PUT, DELETE): 30 requests/minute
- **Read Operations** (GET): 100 requests/minute
- **Health Checks**: No limit

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703419200
```

When rate limit is exceeded:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1703419230

{
  "error": "Rate limit exceeded",
  "retry_after": 30,
  "limit": 100
}
```

## Security

### Authentication

All endpoints (except `/health*`) require valid JWT Bearer token:

```
Authorization: Bearer <access_token>
```

### Token Validation

Tokens are validated for:
- Signature (RS256 with JWKS)
- Expiration
- Issuer (Microsoft Entra ID)
- Audience (API Application ID URI)
- Required scope (`access_as_user`)

### Security Headers

All responses include security headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
```

## Performance

### Monitoring

Performance monitoring is built-in:

- Request/response logging with duration
- Slow operation detection (>1s warning)
- Correlation IDs for distributed tracing
- Performance metrics collection

### Response Times

Target response times:

- Health checks: < 50ms
- GET operations: < 200ms
- POST/PUT operations: < 500ms
- DELETE operations: < 300ms

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    oid VARCHAR NOT NULL UNIQUE,
    display_name VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Blog Posts Table

```sql
CREATE TABLE blog_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id)
);
```

## Development

### Running Locally

```bash
# Install dependencies
cd api
poetry install

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run development server
poetry run python -m src.main
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test suite
poetry run pytest tests/unit
poetry run pytest tests/integration
```

### Code Quality

```bash
# Format code
poetry run black src tests
poetry run isort src tests

# Lint code
poetry run ruff check src tests

# Type checking
poetry run mypy src
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security best practices and vulnerability reporting.

## Support

For issues and questions:
- Review API documentation
- Check [troubleshooting guide](../README.md#troubleshooting)
- Open a GitHub issue

---

**API Version:** v1  
**Last Updated:** 2024-12-24  
**Status:** Production Ready
