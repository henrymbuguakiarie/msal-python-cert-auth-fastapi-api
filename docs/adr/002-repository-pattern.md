# ADR-002: Repository Pattern for Data Access

Date: 2024-12-24

## Status

Accepted

## Context

The application needs a clean separation between business logic and data access. Direct database access in route handlers leads to:

- Tight coupling between layers
- Difficult testing (hard to mock database)
- Code duplication across endpoints
- Poor maintainability
- Violates Single Responsibility Principle

## Decision

Implement the Repository Pattern to abstract data access operations.

**Architecture:**
```
Routes (API Layer)
    ↓
Services (Business Logic)
    ↓
Repositories (Data Access)
    ↓
Database (SQLModel/SQLAlchemy)
```

**Implementation Details:**
- Create `UserRepository` and `BlogPostRepository` classes
- Repositories handle all database CRUD operations
- Services coordinate repositories and implement business rules
- Routes delegate to services and handle HTTP concerns

## Consequences

### Positive Consequences

- **Testability**: Easy to mock repositories for unit testing services
- **Maintainability**: Clear separation of concerns
- **Reusability**: Repository methods can be reused across services
- **Flexibility**: Easy to change database implementation
- **Clean Code**: Each layer has single responsibility

### Negative Consequences

- **More Code**: Requires additional abstraction layers
- **Learning Curve**: Team needs to understand the pattern
- **Indirection**: More layers to trace through during debugging
- **Over-engineering Risk**: May be overkill for very simple apps

## Alternatives Considered

### 1. Active Record Pattern (SQLModel Default)
- **Pros**: Less code, simpler for small apps
- **Cons**: Tight coupling, harder to test, violates SRP
- **Decision**: Rejected - not scalable for production

### 2. Data Mapper Pattern (Pure SQLAlchemy)
- **Pros**: Complete separation, ultimate flexibility
- **Cons**: Much more complex, steeper learning curve
- **Decision**: Rejected - repository pattern provides good balance

### 3. Direct Database Access in Routes
- **Pros**: Fastest to implement, minimal abstraction
- **Cons**: Poor maintainability, untestable, code duplication
- **Decision**: Rejected - unsuitable for production

## Implementation Example

```python
# Repository Layer
class BlogPostRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, post_id: int) -> BlogPost | None:
        return self.session.get(BlogPost, post_id)

# Service Layer
class BlogPostService:
    def __init__(self, session: Session):
        self.repository = BlogPostRepository(session)
    
    def get_post(self, post_id: int) -> BlogPost:
        post = self.repository.get_by_id(post_id)
        if not post:
            raise ResourceNotFoundError("BlogPost", post_id)
        return post

# Route Layer
@router.get("/{post_id}")
async def get_post(post_id: int, session: Session = Depends(get_session)):
    service = BlogPostService(session)
    return service.get_post(post_id)
```

## References

- [Martin Fowler - Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Microsoft - Repository Pattern](https://docs.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design)
- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
