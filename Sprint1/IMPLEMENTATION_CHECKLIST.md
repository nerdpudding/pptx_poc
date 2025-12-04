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
| Project Setup | 5 | 0 | 0% |
| Backend + Container | 22 | 0 | 0% |
| PPTX Generator + Container | 17 | 0 | 0% |
| Frontend + Container | 22 | 0 | 0% |
| Integration & Testing | 12 | 0 | 0% |
| **Total** | **78** | **0** | **0%** |

---

## Phase 0: Project Setup

> **Do this first before any development**

- [ ] Create `frontend/static/` directory
- [ ] Create `orchestrator/api/` directory
- [ ] Create `pptx-generator/templates/` directory
- [ ] Create initial `docker-compose.yml` skeleton
- [ ] Verify Ollama is running and accessible

---

## Phase 1: Backend API + Container

> **Create code and Dockerfile together - test in container immediately**

### Orchestrator Setup
- [ ] Create `orchestrator/Dockerfile` for Python/FastAPI
- [ ] Create `orchestrator/requirements.txt` (fastapi, uvicorn, httpx, pydantic)
- [ ] Add orchestrator service to `docker-compose.yml`
- [ ] Test container builds: `docker-compose build orchestrator`

### FastAPI Application
- [ ] Create `orchestrator/main.py` with FastAPI app
- [ ] Create `orchestrator/config.py` for environment variables
- [ ] Create `orchestrator/api/models.py` (request/response models)
- [ ] Create `orchestrator/api/routes.py` (API endpoints)

### API Endpoints
- [ ] Implement `POST /api/v1/generate` endpoint
- [ ] Add request validation (topic required)
- [ ] Add response formatting
- [ ] Implement error handling middleware
- [ ] Add `GET /health` endpoint

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
- [ ] Create `pptx-generator/Dockerfile` for Python
- [ ] Create `pptx-generator/requirements.txt` (fastapi, uvicorn, python-pptx)
- [ ] Add pptx-generator service to `docker-compose.yml`
- [ ] Test container builds: `docker-compose build pptx-generator`

### Core Service
- [ ] Create `pptx-generator/generator.py` with FastAPI app
- [ ] Create `pptx-generator/config.py` for configuration
- [ ] Implement `POST /generate` endpoint (receives JSON, returns file ID)
- [ ] Implement `GET /download/{file_id}` endpoint
- [ ] Add `GET /health` endpoint

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
- [ ] Create `frontend/Dockerfile` for nginx:alpine
- [ ] Create `frontend/nginx.conf` with API proxy rules
- [ ] Add frontend service to `docker-compose.yml`
- [ ] Test container builds: `docker-compose build frontend`

### HTML Structure
- [ ] Create `frontend/static/index.html`
- [ ] Add input field for presentation topic
- [ ] Add submit button
- [ ] Add download button (hidden initially)
- [ ] Add error message container
- [ ] Add loading spinner element
- [ ] Add responsive meta tags

### CSS Styling
- [ ] Create `frontend/static/style.css`
- [ ] Style layout and form elements
- [ ] Style loading spinner animation
- [ ] Style error messages
- [ ] Add responsive design
- [ ] Add professional color scheme

### JavaScript Functionality
- [ ] Create `frontend/static/app.js`
- [ ] Implement form submission handler
- [ ] Add fetch call to `/api/v1/generate`
- [ ] Implement response handling
- [ ] Add download functionality
- [ ] Implement error display
- [ ] Add input validation
- [ ] Add loading state management

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
| 1 | Create project folders | `ls -la` |
| 2 | Create docker-compose.yml skeleton | `docker-compose config` |
| 3 | Backend code + Dockerfile | `docker-compose up orchestrator` |
| 4 | PPTX Generator code + Dockerfile | `docker-compose up pptx-generator` |
| 5 | Frontend code + Dockerfile | `docker-compose up frontend` |
| 6 | Full integration | `docker-compose up` |

---

## Task Status Legend

| Symbol | Status |
|--------|--------|
| `[ ]` | Not Started |
| `[x]` | Complete |

> **Note:** Mark tasks with `[x]` as you complete them. Update the progress table at the top accordingly.
