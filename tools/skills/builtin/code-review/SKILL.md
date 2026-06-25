---
name: code-review
description: Python code review best practices for generated modules
triggers: [review, check, audit, quality, lint, refactor]
---

# Code Review Standards

## Style
- Follow Google Python Style Guide
- Use type hints on all public functions and methods
- Write docstrings for all public modules, classes, and methods
- Maximum line length: 120 characters
- Use f-strings over format() or %

## Structure
- Group imports: stdlib → third-party → local (blank line between groups)
- `__all__` should be defined in `__init__.py` files
- Prefer dataclasses or Pydantic models for data structures

## Error Handling
- Catch specific exceptions, never bare `except:`
- Include error context in exception messages
- Use custom exception classes for domain errors

## Security
- No hardcoded secrets or API keys
- Validate all external input before use
- Use parameterized queries for database operations
- Never use `eval()` or `exec()` on user input

## Testing
- Write docstring examples for public APIs
- Use pytest fixtures for setup/teardown
- Test both success and error paths
