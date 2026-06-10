# ASE — API Contracts

All services expose OpenAPI/Swagger at `GET /docs` and `GET /openapi.json`.
The API Gateway aggregates all schemas at `GET /api/docs`.

Base URL pattern: `https://{domain}/api/{service}/v1/{resource}`

---

## Auth Service — :8001

### Authentication
```
POST   /api/auth/v1/register
       Body: {email, password, full_name}
       Returns: {user, access_token, refresh_token}

POST   /api/auth/v1/login
       Body: {email, password}
       Returns: {user, access_token, refresh_token}

POST   /api/auth/v1/refresh
       Cookie: refresh_token OR Body: {refresh_token}
       Returns: {access_token, refresh_token}

POST   /api/auth/v1/logout
       Header: Authorization Bearer
       Returns: 204

POST   /api/auth/v1/verify-email
       Body: {token}
       Returns: 200

POST   /api/auth/v1/forgot-password
       Body: {email}
       Returns: 200

POST   /api/auth/v1/reset-password
       Body: {token, new_password}
       Returns: 200
```

### Users
```
GET    /api/auth/v1/me
       Returns: UserResponse

PUT    /api/auth/v1/me
       Body: {full_name, timezone, avatar_url}
       Returns: UserResponse

PUT    /api/auth/v1/me/password
       Body: {current_password, new_password}
       Returns: 200
```

### API Keys
```
GET    /api/auth/v1/api-keys
       Returns: ApiKey[]

POST   /api/auth/v1/api-keys
       Body: {name, scopes[], expires_at?}
       Returns: {api_key (shown once), key_prefix}

DELETE /api/auth/v1/api-keys/{id}
       Returns: 204
```

### Stores
```
GET    /api/auth/v1/stores
       Returns: Store[]

POST   /api/auth/v1/stores
       Body: {name, shopify_domain, shopify_access_token}
       Returns: Store

GET    /api/auth/v1/stores/{id}
       Returns: Store

PUT    /api/auth/v1/stores/{id}
       Body: {name, settings}
       Returns: Store

DELETE /api/auth/v1/stores/{id}
       Returns: 204

POST   /api/auth/v1/stores/{id}/test-connection
       Returns: {ok: bool, shopify_plan, currency}
```

---

## Product Hunter — :8002

### Candidates
```
GET    /api/hunter/v1/candidates
       Query: store_id, status, source, min_score, max_score, limit, offset, sort
       Returns: Paginated<ProductCandidate>

GET    /api/hunter/v1/candidates/{id}
       Returns: ProductCandidateDetail

PATCH  /api/hunter/v1/candidates/{id}/approve
       Body: {store_id?}
       Returns: ProductCandidate

PATCH  /api/hunter/v1/candidates/{id}/reject
       Body: {reason}
       Returns: ProductCandidate

DELETE /api/hunter/v1/candidates/{id}
       Returns: 204
```

### Jobs
```
POST   /api/hunter/v1/jobs/hunt
       Body: {store_id?, sources[]?, force: bool}
       Returns: {task_id}

GET    /api/hunter/v1/jobs/{task_id}
       Returns: {status, progress, result?}

GET    /api/hunter/v1/jobs/history
       Query: store_id, limit
       Returns: Task[]
```

### Sources Config
```
GET    /api/hunter/v1/sources
       Returns: SourceConfig[]

PUT    /api/hunter/v1/sources/{source_name}
       Body: {enabled, priority, config}
       Returns: SourceConfig
```

---

## Marketing Service — :8003

### Assets
```
GET    /api/marketing/v1/assets
       Query: store_id, candidate_id, status, limit, offset
       Returns: Paginated<MarketingAsset>

GET    /api/marketing/v1/assets/{id}
       Returns: MarketingAsset

PATCH  /api/marketing/v1/assets/{id}
       Body: {brand_name?, tagline?, bullets?, faqs?, ...}
       Returns: MarketingAsset

PATCH  /api/marketing/v1/assets/{id}/approve
       Returns: MarketingAsset

DELETE /api/marketing/v1/assets/{id}
       Returns: 204
```

### Generation
```
POST   /api/marketing/v1/generate
       Body: {candidate_id, store_id, content_types[]?, model_tier?}
       Returns: {task_id}

POST   /api/marketing/v1/regenerate/{asset_id}/{section}
       Body: {instructions?}
       Returns: {task_id}

GET    /api/marketing/v1/jobs/{task_id}
       Returns: {status, progress, asset_id?}
```

---

## Image Pipeline — :8004

### Images
```
GET    /api/images/v1/images
       Query: candidate_id, store_id, type, status, limit, offset
       Returns: Paginated<GeneratedImage>

GET    /api/images/v1/images/{id}
       Returns: GeneratedImage

PATCH  /api/images/v1/images/{id}/approve
       Returns: GeneratedImage

DELETE /api/images/v1/images/{id}
       Returns: 204
```

### Generation
```
POST   /api/images/v1/generate
       Body: {candidate_id, store_id, types[]?, provider?}
       Returns: {task_id, image_ids[]}

POST   /api/images/v1/regenerate/{image_id}
       Body: {prompt_override?}
       Returns: {task_id}

GET    /api/images/v1/jobs/{task_id}
       Returns: {status, completed, total, image_ids[]}
```

---

## Shopify Publisher — :8005

### Published Products
```
GET    /api/publisher/v1/products
       Query: store_id, status, limit, offset
       Returns: Paginated<ProductPublished>

GET    /api/publisher/v1/products/{id}
       Returns: ProductPublished

POST   /api/publisher/v1/products/{id}/sync
       Returns: {task_id}

PATCH  /api/publisher/v1/products/{id}/status
       Body: {status: active|archived}
       Returns: ProductPublished

DELETE /api/publisher/v1/products/{id}
       Returns: 204
```

### Publish Flow
```
POST   /api/publisher/v1/publish
       Body: {candidate_id, store_id, publish_immediately?: bool}
       Returns: {task_id}

GET    /api/publisher/v1/jobs/{task_id}
       Returns: {status, shopify_product_id?, errors[]}
```

### Webhooks
```
POST   /api/publisher/v1/webhooks/shopify
       Header: X-Shopify-Hmac-SHA256
       Body: Shopify webhook payload
       Returns: 200
```

---

## Analytics Service — :8006

### Analytics
```
GET    /api/analytics/v1/summary
       Query: store_id, date_from, date_to
       Returns: AnalyticsSummary {revenue, profit, roas, orders, ...}

GET    /api/analytics/v1/timeseries
       Query: store_id, metric, granularity, date_from, date_to
       Returns: {date, value}[]

GET    /api/analytics/v1/products/{product_id}/performance
       Query: store_id, date_from, date_to
       Returns: ProductPerformance

GET    /api/analytics/v1/campaigns
       Query: store_id, status, platform, limit, offset
       Returns: Paginated<Campaign>

POST   /api/analytics/v1/campaigns
       Body: {store_id, product_id, name, platform, ...}
       Returns: Campaign

PATCH  /api/analytics/v1/campaigns/{id}
       Body: {status?, budget_daily?, targeting?}
       Returns: Campaign
```

### Decisions
```
GET    /api/analytics/v1/decisions
       Query: store_id, decision_type, date
       Returns: Decision[]

POST   /api/analytics/v1/decisions/{analytics_id}/apply
       Body: {confirmed: true}
       Returns: Decision
```

---

## Notifications Service — :8007

```
GET    /api/notifications/v1/notifications
       Query: is_read?, event_type?, limit, offset
       Returns: Paginated<Notification>

POST   /api/notifications/v1/notifications/{id}/read
       Returns: Notification

POST   /api/notifications/v1/notifications/read-all
       Returns: {count: int}

GET    /api/notifications/v1/settings
       Returns: NotificationSettings

PUT    /api/notifications/v1/settings
       Body: {channels, events, email?, discord_webhook?, telegram_chat_id?, slack_webhook?}
       Returns: NotificationSettings
```

---

## API Gateway — :8000

### Special Endpoints
```
GET    /api/health
       Returns: {status: ok, services: {auth: ok, hunter: ok, ...}}

GET    /api/docs
       Returns: Aggregated Swagger UI

GET    /api/events/stream
       Header: Authorization Bearer
       Query: store_id
       Returns: SSE stream {event: string, data: JSON}

GET    /metrics
       Returns: Prometheus metrics (internal only)
```

---

## Common Response Shapes

### Pagination
```json
{
  "items": [...],
  "total": 100,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### Error Response
```json
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product with id abc123 not found",
    "details": {},
    "request_id": "req_abc123"
  }
}
```

### Task Response
```json
{
  "task_id": "uuid",
  "status": "pending | started | success | failure",
  "progress": 0.65,
  "result": null,
  "error": null,
  "created_at": "ISO8601",
  "completed_at": null
}
```

---

## HTTP Status Codes Used

| Code | Meaning |
|---|---|
| 200 | Success with body |
| 201 | Created |
| 204 | Success, no body |
| 400 | Validation error |
| 401 | Not authenticated |
| 403 | Not authorized (valid auth, wrong role/store) |
| 404 | Resource not found |
| 409 | Conflict (duplicate) |
| 422 | Unprocessable entity (Pydantic validation) |
| 429 | Rate limited |
| 500 | Internal server error |
| 502 | Upstream service unavailable |
| 503 | Service unavailable (health check failing) |
