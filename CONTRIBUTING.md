# Contributing Guide

Thank you for your interest in contributing to the MSAL Python Certificate Authentication project! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Architecture Guidelines](#architecture-guidelines)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Prioritize community well-being

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Poetry for dependency management
- Git for version control
- Microsoft Entra ID tenant (for integration testing)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-org/msal-python-cert-auth-fastapi-api.git
cd msal-python-cert-auth-fastapi-api

# Install dependencies
make install

# Install pre-commit hooks
make pre-commit

# Set up environment variables
cp api/.env.example api/.env
cp client/.env.example client/.env
# Edit .env files with your configuration
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/modifications

### 2. Make Changes

Write code following our [code standards](#code-standards).

### 3. Test Your Changes

```bash
# Run all tests
make test

# Run specific test suite
make test-api
make test-integration

# Check code coverage
cd api && poetry run pytest --cov=src --cov-report=html
```

### 4. Format and Lint

```bash
# Format code
make format

# Run linters
make lint

# Run security checks
make security
```

### 5. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add user profile endpoint

- Add GET /profile endpoint for user info
- Add ProfileResponse schema
- Add tests for profile endpoint
- Update API documentation
```

**Commit Message Format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/modifications
- `chore`: Build/tooling changes

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Standards

### Python Code Style

We follow PEP 8 with these tools:

- **Black** (100 character line length)
- **isort** (import sorting)
- **Ruff** (linting)

```bash
# Format code
poetry run black src tests
poetry run isort src tests

# Check formatting
poetry run black --check src tests
poetry run isort --check-only src tests

# Lint code
poetry run ruff check src tests
```

### Type Hints

Use type hints for all functions and methods:

```python
def get_user(user_id: int) -> User | None:
    """Get user by ID.
    
    Args:
        user_id: User ID
        
    Returns:
        User if found, None otherwise
    """
    return db.get(User, user_id)
```

### Docstrings

Use Google-style docstrings:

```python
def create_post(title: str, content: str, author_id: int) -> BlogPost:
    """Create a new blog post.
    
    Args:
        title: Post title (1-200 characters)
        content: Post content (required)
        author_id: Author's user ID
        
    Returns:
        Created blog post with ID and timestamps
        
    Raises:
        ValidationError: If title or content is invalid
        ResourceNotFoundError: If author not found
        
    Example:
        >>> post = create_post("Hello", "World", 1)
        >>> print(post.id)
        42
    """
    # Implementation
```

### Error Handling

Use custom exception classes:

```python
from .exceptions import ResourceNotFoundError, AuthorizationError

def update_post(post_id: int, user_id: int, data: dict) -> BlogPost:
    post = repository.get_by_id(post_id)
    if not post:
        raise ResourceNotFoundError("BlogPost", post_id)
    
    if post.author_id != user_id:
        raise AuthorizationError("Cannot modify another user's post")
    
    return repository.update(post_id, data)
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Unit tests (isolated, mocked)
│   ├── test_models.py
│   ├── test_repositories.py
│   └── test_services.py
└── integration/       # Integration tests (full stack)
    └── test_endpoints.py
```

### Writing Tests

```python
import pytest
from src.models import BlogPost
from src.repositories import BlogPostRepository

class TestBlogPostRepository:
    """Test suite for BlogPostRepository."""
    
    def test_create_post_success(self, db_session):
        """Test successful post creation."""
        # Arrange
        repo = BlogPostRepository(db_session)
        
        # Act
        post = repo.create(
            title="Test Post",
            content="Test content",
            author_id=1
        )
        
        # Assert
        assert post.id is not None
        assert post.title == "Test Post"
        assert post.content == "Test content"
    
    def test_get_nonexistent_post(self, db_session):
        """Test getting post that doesn't exist."""
        repo = BlogPostRepository(db_session)
        post = repo.get_by_id(999)
        assert post is None
```

### Test Coverage

Maintain >80% code coverage:

```bash
# Generate coverage report
poetry run pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass locally
2. ✅ Code is formatted and linted
3. ✅ New tests added for new features
4. ✅ Documentation updated
5. ✅ Commit messages are clear
6. ✅ Branch is up to date with main

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests pass locally
```

### Review Process

1. Automated checks must pass (CI/CD)
2. At least one approval required
3. Address review comments
4. Squash commits before merge (if needed)

## Architecture Guidelines

### Layered Architecture

Follow the established pattern:

```
Routes (API Layer)
  ↓ Call services
Services (Business Logic)
  ↓ Use repositories
Repositories (Data Access)
  ↓ Query database
Database (SQLModel/SQLAlchemy)
```

### Adding New Features

#### 1. New API Endpoint

```python
# 1. Add model/schema (models.py)
class FeatureResponse(BaseModel):
    id: int
    name: str

# 2. Add repository method (repositories.py)
class FeatureRepository:
    def get_by_id(self, id: int) -> Feature | None:
        return self.session.get(Feature, id)

# 3. Add service method (services.py)
class FeatureService:
    def get_feature(self, id: int) -> Feature:
        feature = self.repository.get_by_id(id)
        if not feature:
            raise ResourceNotFoundError("Feature", id)
        return feature

# 4. Add route (routes.py)
@router.get("/{id}", response_model=FeatureResponse)
async def get_feature(id: int, session: Session = Depends(get_session)):
    service = FeatureService(session)
    return service.get_feature(id)

# 5. Add tests
def test_get_feature_success(db_session):
    # Test implementation
```

### Architecture Decision Records

For significant architectural changes, create an ADR:

```bash
# Create new ADR
cp docs/adr/000-template.md docs/adr/003-your-decision.md
# Edit with your decision details
```

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing documentation
- Review closed issues/PRs

Thank you for contributing! 🎉
