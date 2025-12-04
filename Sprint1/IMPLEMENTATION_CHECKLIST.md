# Sprint 1 Implementation Checklist

> **This is the single source of truth for all Sprint 1 tasks.**
> For daily progress tracking, see [DAILY_LOG.md](DAILY_LOG.md)

## Development Philosophy: Container-First

> **All services run in Docker containers.** For each component:
> 1. Write code + Dockerfile together
> 2. Add to docker-compose.yml
> 3. Test via `docker-compose up`

---

## Master Progress

| Category | Total | Completed | Percentage |
|----------|-------|-----------|------------|
| Project Setup | 9 | 9 | 100% |
| Backend + Container | 22 | 12 | 55% |
| PPTX Generator + Container | 17 | 8 | 47% |
| Frontend + Container | 22 | 14 | 64% |
| Integration & Testing | 12 | 0 | 0% |
| **Total** | **82** | **43** | **52%** |

---

## Phase 0: Project Setup (✅ COMPLETE)

> **Docker infrastructure is ready.** See [QUICK_INSTALL.md](../QUICK_INSTALL.md) for setup.

- [x] Create `docker-compose.yml` (main stack, external Ollama network)
- [x] Create `docker-compose.ollama.yml` (optional standalone Ollama)
- [x] Create `.env.example` with port/model configuration
- [x] Create `QUICK_INSTALL.md` setup guide
- [x] Create `frontend/static/` directory
- [x] Create `orchestrator/api/` directory
- [x] Create `pptx-generator/templates/` directory
- [x] Configure `.env` for your environment
- [x] Verify Ollama is connected to `ollama-network`

---

## Phase 1: Backend API + Container

> **Create code and Dockerfile together - test in container immediately**

### Orchestrator Setup
- [x] Create `orchestrator/Dockerfile` for Python/FastAPI
- [x] Create `orchestrator/requirements.txt` (fastapi, uvicorn, httpx, pydantic)
- [x] Add orchestrator service to `docker-compose.yml`
- [ ] Test container builds: `docker-compose build orchestrator`

### FastAPI Application
- [x] Create `orchestrator/main.py` with FastAPI app
- [x] Create `orchestrator/config.py` for environment variables (pydantic-settings)
- [x] Create `orchestrator/api/models.py` (request/response models with Field validation)
- [x] Create `orchestrator/api/routes.py` (API endpoints with dependency injection)

### API Endpoints
- [x] Implement `POST /api/v1/generate` endpoint
- [x] Add request validation (topic required, max 500 chars)
- [x] Add response formatting (success, fileId, downloadUrl, preview)
- [x] Implement error handling middleware (validation + general exceptions)
- [x] Add `GET /health` endpoint

### Ollama Integration
- [ ] Create `orchestrator/api/ollama_client.py`
- [ ] Implement async HTTP client for Ollama
- [ ] Build prompt template for presentation generation
- [ ] Add response parsing (extract JSON)
- [ ] Implement timeout handling
- [ ] Add retry logic for transient failures

### Container Testing
- [ ] Test `docker-compose up orchestrator`
- [ ] Test health endpoint with curl
- [ ] Test generate endpoint with curl
- [ ] Verify Ollama communication works in container

---

## Phase 2: PPTX Generator + Container

> **Create code and Dockerfile together - test in container immediately**

### Generator Setup
- [x] Create `pptx-generator/Dockerfile` for Python
- [x] Create `pptx-generator/requirements.txt` (fastapi, uvicorn, python-pptx)
- [x] Add pptx-generator service to `docker-compose.yml`
- [ ] Test container builds: `docker-compose build pptx-generator`

### Core Service
- [x] Create `pptx-generator/generator.py` with FastAPI app
- [ ] Create `pptx-generator/config.py` for configuration
- [x] Implement `POST /generate` endpoint (receives JSON, returns file ID)
- [x] Implement `GET /download/{file_id}` endpoint (placeholder)
- [x] Add `GET /health` endpoint

### PPTX Generation
- [ ] Create `pptx-generator/templates/basic_template.py`
- [ ] Implement title slide creation
- [ ] Implement content slide creation (with bullets)
- [ ] Implement summary slide creation
- [ ] Add basic styling (fonts, colors)
- [ ] Implement file storage and cleanup

### Container Testing
- [ ] Test `docker-compose up pptx-generator`
- [ ] Test health endpoint with curl
- [ ] Test generate endpoint with sample JSON
- [ ] Verify PPTX file is created correctly

---

## Phase 3: Frontend + Container

> **Create code and Dockerfile together - test in container immediately**

### Frontend Setup
- [x] Create `frontend/Dockerfile` for nginx:alpine
- [x] Create `frontend/nginx.conf` with API proxy rules
- [x] Add frontend service to `docker-compose.yml`
- [ ] Test container builds: `docker-compose build frontend`

### HTML Structure
- [x] Create `frontend/static/index.html`
- [x] Add input field for presentation topic
- [x] Add submit button
- [x] Add download button (hidden initially)
- [x] Add error message container
- [x] Add loading spinner element
- [x] Add responsive meta tags

### CSS Styling
- [x] Create `frontend/static/style.css`
- [x] Style layout and form elements
- [x] Style loading spinner animation
- [x] Style error messages
- [x] Add responsive design
- [x] Add professional color scheme

### JavaScript Functionality
- [x] Create `frontend/static/app.js`
- [x] Implement form submission handler
- [x] Add fetch call to `/api/v1/generate`
- [x] Implement response handling
- [x] Add download functionality
- [x] Implement error display (XSS-safe with textContent)
- [x] Add input validation
- [x] Add loading state management

### Container Testing
- [ ] Test `docker-compose up frontend`
- [ ] Verify nginx serves static files
- [ ] Verify API proxy works correctly

---

## Phase 4: Integration & Testing

> **All services running together: `docker-compose up`**

### End-to-End Testing
- [ ] Test complete workflow (input → generate → download)
- [ ] Test error scenarios (invalid input, Ollama down, etc.)
- [ ] Test timeout handling
- [ ] Test concurrent requests

### Performance Testing
- [ ] Verify response time < 30 seconds
- [ ] Check container memory usage
- [ ] Check Docker image sizes < 200MB each

### Final Validation
- [ ] Test on different browsers
- [ ] Test mobile responsiveness
- [ ] Verify all health endpoints respond
- [ ] Document any known issues

---

## Quick Start: Implementation Order

| Step | What to Do | Test Command |
|------|------------|--------------|
| 1 | Configure environment | `cp .env.example .env` |
| 2 | Setup Ollama network | See [QUICK_INSTALL.md](../QUICK_INSTALL.md) |
| 3 | Create project folders | `mkdir -p frontend/static orchestrator/api pptx-generator/templates` |
| 4 | Backend code + Dockerfile | `docker-compose up orchestrator` |
| 5 | PPTX Generator code + Dockerfile | `docker-compose up pptx-generator` |
| 6 | Frontend code + Dockerfile | `docker-compose up frontend` |
| 7 | Full integration | `docker-compose up` |

## Service Ports

| Service | Host Port | Internal Port | URL |
|---------|-----------|---------------|-----|
| Orchestrator | 5100 | 8000 | http://localhost:5100 |
| PPTX Generator | 5101 | 8001 | http://localhost:5101 |
| Frontend | 5102 | 80 | http://localhost:5102 |

> Ports configurable via `.env`. See [QUICK_INSTALL.md](../QUICK_INSTALL.md).

---

## Task Status Legend

| Symbol | Status |
|--------|--------|
| `[ ]` | Not Started |
| `[x]` | Complete |

> **Note:** Mark tasks with `[x]` as you complete them. Update the progress table at the top accordingly.
