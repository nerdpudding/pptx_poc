# Technical Documentation

> **For developers working on this codebase.** For setup instructions, see [QUICK_INSTALL.md](QUICK_INSTALL.md).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Configuration Hierarchy](#configuration-hierarchy)
3. [SOLID Principles Applied](#solid-principles-applied)
4. [Service Details](#service-details)
5. [API Contract](#api-contract)
6. [Security Considerations](#security-considerations)
7. [Code Patterns](#code-patterns)

---

## Architecture Overview

### Container-First Development

All services run in Docker containers. This ensures:
- Consistent environments across development/production
- Easy dependency management
- Isolated services with clear boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Frontend   │───▶│ Orchestrator │───▶│    PPTX      │  │
│  │   (nginx)    │    │  (FastAPI)   │    │  Generator   │  │
│  │   :5102      │    │    :5100     │    │    :5101     │  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘  │
│                             │                               │
│                             ▼                               │
│                    ┌──────────────┐                         │
│                    │    Ollama    │  (external network)     │
│                    │   :11434     │                         │
│                    └──────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Service Responsibilities

| Service | Technology | Purpose |
|---------|------------|---------|
| **Frontend** | nginx:alpine | Static file serving, API proxy |
| **Orchestrator** | Python/FastAPI | Business logic, Ollama communication |
| **PPTX Generator** | Python/FastAPI | PowerPoint file creation |
| **Ollama** | External | LLM inference (runs on GPU) |

### Network Architecture

- **internal**: Bridge network for service-to-service communication
- **ollama-network**: External network connecting to Ollama

Ollama runs externally so it can be shared across projects and doesn't need to reload models.

---

## Configuration Hierarchy

Configuration follows a **layered approach** where each layer can override the previous:

```
┌─────────────────────────────────────────┐
│  1. Code Defaults (config.py)           │  Fallback values
├─────────────────────────────────────────┤
│  2. Environment Variables (.env)        │  Deployment config
├─────────────────────────────────────────┤
│  3. API Request Parameters              │  Per-request override
└─────────────────────────────────────────┘
        ▲
        │ Higher layers win
```

### Example: Ollama Temperature

| Layer | Where | Value |
|-------|-------|-------|
| Code Default | `config.py` | `ollama_temperature: float = 0.15` |
| Environment | `.env` | `OLLAMA_TEMPERATURE=0.2` |
| API Request | JSON body | `{"temperature": 0.3}` |

**Result:** If all three are set, `0.3` is used (API request wins).

### Why This Pattern?

1. **Development:** Works out-of-the-box with sensible defaults
2. **Deployment:** Customize via `.env` without code changes
3. **Runtime:** Users can fine-tune per request via UI

### Environment Variables

All Ollama-related settings:

```bash
# .env file
OLLAMA_HOST=http://ollama:11434      # Ollama API endpoint
OLLAMA_MODEL=ministral-3-14b-...     # Model to use
OLLAMA_TIMEOUT=120                    # Request timeout (seconds)
OLLAMA_TEMPERATURE=0.15               # Sampling temperature
OLLAMA_NUM_CTX=122880                 # Context window size
```

### Config Loading (pydantic-settings)

```python
# orchestrator/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_temperature: float = 0.15  # Default if not in .env

    class Config:
        env_file = ".env"  # Auto-load from .env file
```

---

## SOLID Principles Applied

### Single Responsibility

Each file has one job:

```
orchestrator/
├── main.py          # App setup, middleware, router inclusion
├── config.py        # Environment configuration only
└── api/
    ├── models.py    # Pydantic models (validation)
    ├── routes.py    # HTTP endpoint handlers
    └── ollama_client.py  # Ollama communication only
```

### Open/Closed

- **Config:** Add new settings without changing existing code
- **Routes:** Add new endpoints without modifying existing ones
- **Models:** Extend with optional fields (backward compatible)

### Dependency Inversion

FastAPI's `Depends()` for dependency injection:

```python
# routes.py
@router.post("/api/v1/generate")
async def generate_presentation(
    request: GenerateRequest,
    settings: Settings = Depends(get_settings)  # Injected
) -> GenerateResponse:
    ...
```

### Interface Segregation

Small, focused Pydantic models instead of one large model:

```python
# Instead of one giant model:
class GenerateRequest(BaseModel):
    topic: str
    language: Optional[str] = "en"
    temperature: Optional[float] = None  # Optional override
    num_ctx: Optional[int] = None
    slides: Optional[int] = None
```

---

## Service Details

### Orchestrator (orchestrator/)

**Entry point:** `main.py`

```python
# Slim main.py - just setup
app = FastAPI(...)
app.add_middleware(CORSMiddleware, ...)
app.include_router(router)
```

**Request flow:**
1. Request hits `/api/v1/generate`
2. Pydantic validates input (`models.py`)
3. Route handler processes (`routes.py`)
4. Ollama client generates content (`ollama_client.py`)
5. Response formatted and returned

**Key files:**

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app setup, CORS, error handlers |
| `config.py` | pydantic-settings configuration |
| `api/models.py` | Request/response Pydantic models |
| `api/routes.py` | API endpoint handlers |
| `api/ollama_client.py` | Async Ollama HTTP client |

### Frontend (frontend/)

**Technology:** nginx:alpine (lightweight)

**Key features:**
- Static file serving with caching
- API proxy to orchestrator (avoids CORS issues)
- Health endpoint for container orchestration

**Proxy configuration:**

```nginx
# frontend/nginx.conf
location /api/ {
    proxy_pass http://orchestrator:8000/api/;
    proxy_read_timeout 60s;  # Allow time for LLM generation
}
```

### PPTX Generator (pptx-generator/)

**Technology:** Python + python-pptx

**Endpoints:**
- `POST /generate` - Create PPTX from JSON
- `GET /download/{file_id}` - Download generated file
- `GET /health` - Health check

---

## API Contract

### Generate Presentation

```http
POST /api/v1/generate
Content-Type: application/json

{
    "topic": "AI in Healthcare",
    "language": "en",
    "temperature": 0.15,    // optional
    "num_ctx": 122880,      // optional
    "slides": 5             // optional
}
```

**Response (success):**

```json
{
    "success": true,
    "fileId": "uuid-here",
    "downloadUrl": "/api/v1/download/uuid-here",
    "preview": {
        "title": "AI in Healthcare",
        "slides": [
            {
                "type": "title",
                "heading": "AI in Healthcare",
                "subheading": "Transforming Patient Care"
            },
            {
                "type": "content",
                "heading": "Key Applications",
                "bullets": ["Diagnosis", "Treatment planning", "..."]
            }
        ]
    }
}
```

**Response (error):**

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Topic must be between 1 and 500 characters"
    }
}
```

### Validation Rules

| Field | Constraint |
|-------|------------|
| `topic` | Required, 1-500 characters |
| `language` | Optional, max 10 chars, default "en" |
| `temperature` | Optional, 0.0-2.0 |
| `num_ctx` | Optional, 4096-131072 |
| `slides` | Optional, 3-10 |

---

## Security Considerations

### Input Validation

All input is validated with Pydantic:

```python
class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
```

### XSS Prevention (Frontend)

Always use `textContent` instead of `innerHTML`:

```javascript
// SAFE - escapes HTML
element.textContent = userInput;

// DANGEROUS - allows XSS
element.innerHTML = userInput;  // Never do this!
```

### Error Handling

Never expose internal errors to clients:

```python
except Exception as e:
    logger.error(f"Internal error: {e}")  # Log internally
    raise HTTPException(
        status_code=500,
        detail={"error": {"message": "Something went wrong"}}  # Generic message
    )
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Configurable
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Code Patterns

### Async/Await

All I/O operations are async:

```python
async def generate_presentation(...):
    response = await self._send_ollama_request(prompt)
    return response
```

### Retry Logic (tenacity)

Ollama requests use exponential backoff:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
)
async def generate_presentation(...):
    ...
```

### JSON Response Cleaning

LLMs sometimes wrap JSON in markdown:

```python
def _clean_json_response(self, text: str) -> str:
    # Remove ```json ... ``` blocks
    text = re.sub(r'```json\s*\n?', '', text)
    text = re.sub(r'```\s*\n?', '', text)

    # Extract JSON object
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        return text[start:end + 1]
    return text
```

### Factory Pattern for Dependencies

```python
# Factory function
def get_ollama_client() -> OllamaClient:
    settings = get_settings()
    return OllamaClient(settings)

# FastAPI dependency
async def get_ollama_client_dependency() -> OllamaClient:
    client = get_ollama_client()
    async with client:
        yield client
```

---

## File Structure

```
pptx_poc/
├── docker-compose.yml          # Main stack definition
├── docker-compose.ollama.yml   # Standalone Ollama (optional)
├── .env.example                # Environment template
├── .env                        # Local config (git-ignored)
│
├── orchestrator/               # Main backend API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI app setup
│   ├── config.py               # pydantic-settings config
│   └── api/
│       ├── __init__.py
│       ├── models.py           # Pydantic models
│       ├── routes.py           # API endpoints
│       └── ollama_client.py    # Ollama HTTP client
│
├── pptx-generator/             # PPTX creation service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── generator.py            # FastAPI app + PPTX logic
│
├── frontend/                   # Static frontend
│   ├── Dockerfile
│   ├── nginx.conf              # Proxy + static serving
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── app.js
│
└── Sprint1/                    # Project management
    ├── IMPLEMENTATION_CHECKLIST.md
    ├── DAILY_LOG.md
    └── SPRINT1_PLAN.md
```

---

## Debugging Tips

### View container logs

```bash
docker compose logs -f orchestrator
docker compose logs -f pptx-generator
```

### Test API directly

```bash
# Health check
curl http://localhost:5100/health

# Generate (with custom params)
curl -X POST http://localhost:5100/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Test", "temperature": 0.2, "slides": 3}'
```

### Access Swagger UI

FastAPI auto-generates API docs:
- http://localhost:5100/docs (Swagger UI)
- http://localhost:5100/redoc (ReDoc)

### Check Ollama connectivity

```bash
# From host
curl http://localhost:11434/api/tags

# From inside orchestrator container
docker compose exec orchestrator curl http://ollama:11434/api/tags
```

---

## Adding New Features

### New API Endpoint

1. Add model in `api/models.py`
2. Add route in `api/routes.py`
3. Update tests (when available)

### New Configuration Option

1. Add to `config.py` with default value
2. Add to `.env.example` with documentation
3. Use in code via `settings.new_option`

### New Frontend Setting

1. Add HTML control in `index.html`
2. Style in `style.css`
3. Wire up in `app.js` (add to `getSettingsValues()`)
4. Add to API request body

---

*Last updated: 2025-12-04*
