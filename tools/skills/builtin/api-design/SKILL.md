---
name: api-design
description: RESTful API design patterns for FastAPI modules
triggers: [api, endpoint, route, rest, fastapi, http, request, response]
---

# API Design Standards

## Endpoint Design
- Use plural nouns for resource names: `/users`, `/orders`
- Use HTTP methods semantically: GET (read), POST (create), PUT (update), DELETE (remove)
- Return appropriate status codes: 200, 201, 204, 400, 404, 422, 500
- Version APIs in the URL: `/v1/users`

## Request/Response
- Use Pydantic models for request bodies and response schemas
- Validate all input with Pydantic validators
- Return consistent JSON structure: `{"data": ..., "error": null}`
- Use query parameters for filtering, pagination, and sorting

## Error Responses
- Return structured error objects: `{"error": {"code": "...", "message": "..."}}`
- Include `detail` field for validation errors (FastAPI default)
- Never expose internal stack traces in production

## Documentation
- Every endpoint must have a docstring with summary, args, returns
- Use FastAPI decorators for OpenAPI spec generation
- Document all possible error responses

## Middleware
- Use CORS middleware for cross-origin requests
- Add request timing middleware
- Implement rate limiting for public endpoints
