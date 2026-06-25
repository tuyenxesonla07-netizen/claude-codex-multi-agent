---
name: testing
description: Testing patterns for Python modules and APIs
triggers: [test, testing, pytest, unit, integration, coverage, assert]
---

# Testing Standards

## Unit Tests
- Test file naming: `test_<module>.py`
- Test function naming: `test_<scenario>_<expected_outcome>`
- Use pytest fixtures for common setup
- Mock external dependencies (LLM calls, database, HTTP)
- Test both happy path and error cases

## Test Structure (Arrange-Act-Assert)
```python
def test_create_user_with_valid_data():
    # Arrange
    data = {"name": "Alice", "email": "alice@example.com"}

    # Act
    result = create_user(data)

    # Assert
    assert result.name == "Alice"
    assert result.email == "alice@example.com"
```

## API Tests
- Use `httpx.AsyncClient` with ASGI transport for FastAPI testing
- Override dependencies with `app.dependency_overrides`
- Test all documented error responses
- Verify response schema matches Pydantic models

## Coverage
- Minimum 80% code coverage for generated modules
- Exclude `__init__.py` files from coverage requirements
- Use `pytest-cov` for coverage reporting

## Fixtures
- Define shared fixtures in `conftest.py`
- Use factory fixtures for creating test data
- Clean up resources in fixture teardown
