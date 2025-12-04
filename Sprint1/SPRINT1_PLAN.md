# Sprint 1: Implementation Plan

## Sprint Overview

**Duration:** 2-3 weeks (flexible)
**Objective:** Implement the core PowerPoint generation functionality based on Sprint 0 research and planning
**Status:** ✅ Sprint 1 Complete

## Development Philosophy: Container-First

> **All services run in Docker containers from day one.**
> No need to install Python, Node, etc. locally - just Docker.

For each component:
1. Write the code
2. Create the Dockerfile immediately
3. Add to docker-compose.yml
4. Build and test via `docker compose up`

---

## Sprint Goals

### Primary Goals
1. **Working frontend interface** - User can input presentation topic and download PPTX
2. **Functional backend API** - Processes requests and generates presentations
3. **Dockerized microservices** - All components run in containers **from the start**
4. **Basic error handling** - Graceful failure modes and user feedback

### Secondary Goals (if time permits)
- Basic presentation preview functionality
- Simple input validation
- Health monitoring endpoints
- Basic logging

---

## Implementation Phases

### Phase 0: Project Setup (✅ COMPLETE)

Docker infrastructure is ready. See [QUICK_INSTALL.md](../QUICK_INSTALL.md) for setup instructions.

```bash
# Create service directories
mkdir -p frontend/static
mkdir -p orchestrator/api
mkdir -p pptx-generator/templates

# Configure environment
cp .env.example .env
# Edit .env to set OLLAMA_MODEL for your GPU VRAM

# Setup Ollama (choose one):
# Option A - Fresh install:
docker compose -f docker-compose.ollama.yml up -d
# Option B - Existing Ollama:
docker network connect ollama-network <your-ollama-container>
```

**Project Structure:**
```
pptx_poc/
├── docker-compose.yml          # Main stack (ports 5100-5102, external Ollama)
├── docker-compose.ollama.yml   # Optional: standalone Ollama for fresh installs
├── .env.example                # Environment template (ports, model config)
├── .env                        # Your local config (git-ignored)
├── QUICK_INSTALL.md            # Setup guide with model recommendations
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── app.js
├── orchestrator/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   └── api/
│       ├── routes.py
│       ├── models.py
│       └── ollama_client.py
└── pptx-generator/
    ├── Dockerfile
    ├── requirements.txt
    ├── generator.py
    ├── config.py
    └── templates/
        └── basic_template.py
```

### Phase 1: Backend API + Container (✅ COMPLETE)
**Estimate:** 3-4 days

Build the orchestrator service with immediate containerization.

**Completed:**
- ✅ `orchestrator/Dockerfile` - Python 3.11 slim + FastAPI
- ✅ `orchestrator/requirements.txt` - Dependencies defined
- ✅ Service added to `docker-compose.yml`
- ✅ `orchestrator/main.py` - FastAPI app (slim, CORS, exception handlers)
- ✅ `orchestrator/config.py` - pydantic-settings for environment configuration
- ✅ `orchestrator/api/__init__.py` - Package initialization
- ✅ `orchestrator/api/models.py` - Pydantic models with Field validation
- ✅ `orchestrator/api/routes.py` - Endpoints with dependency injection
- ✅ `orchestrator/api/ollama_client.py` - Async HTTP client for Ollama with streaming
- ✅ `orchestrator/api/pptx_client.py` - Async HTTP client for PPTX Generator
- ✅ `orchestrator/api/chat_routes.py` - Guided Mode chat endpoints

**Test:** `docker compose up orchestrator` then curl the endpoints

### Phase 2: PPTX Generator + Container (✅ COMPLETE)
**Estimate:** 2-3 days

Build the PPTX generator service with immediate containerization.

**Completed:**
- ✅ `pptx-generator/Dockerfile` - Python 3.11 slim + python-pptx
- ✅ `pptx-generator/requirements.txt` - Dependencies defined
- ✅ Service added to `docker-compose.yml`
- ✅ `pptx-generator/generator.py` - FastAPI app with generate/download endpoints
- ✅ `pptx-generator/slide_builder.py` - SlideBuilder class with python-pptx
- ✅ Professional styling (blue color scheme, 16:9 format)
- ✅ Dynamic slide support (any number of slides)
- ✅ File storage in `/app/output/`

**Test:** `docker compose up pptx-generator` then test generation

### Phase 3: Frontend + Container (✅ COMPLETE)
**Estimate:** 2-3 days

Build the frontend with immediate containerization.

**Completed:**
- ✅ `frontend/Dockerfile` - nginx:alpine
- ✅ `frontend/nginx.conf` - API proxy, static files, security headers
- ✅ Service added to `docker-compose.yml`
- ✅ `frontend/static/index.html` - Clean HTML with links to CSS/JS
- ✅ `frontend/static/style.css` - CSS variables, responsive design
- ✅ `frontend/static/app.js` - Real API calls, XSS-safe DOM handling
- ✅ Quick Mode: topic → generate → download
- ✅ Guided Mode: AI chat → draft → generate → download
- ✅ Debug panel for LLM testing

**Test:** `docker compose up frontend` then test in browser 

### Phase 4: Integration & Testing (✅ COMPLETE)
**Estimate:** 1-2 days

All services running together in containers.

**Completed:**
- ✅ End-to-end workflow: Quick Mode and Guided Mode
- ✅ PPTX file generation and download working
- ✅ All health endpoints responding
- ✅ Streaming responses through nginx proxy

**Test:** `docker compose up` - full stack testing

---

## Development Order (Docker-First)

| Step | Component | What to Create | How to Test |
|------|-----------|----------------|-------------|
| 1 | Setup | Project folders + docker-compose.yml skeleton | N/A |
| 2 | Backend | Code + Dockerfile together | `docker compose up orchestrator` + curl |
| 3 | PPTX | Code + Dockerfile together | `docker compose up pptx-generator` |
| 4 | Frontend | Code + Dockerfile together | `docker compose up frontend` |
| 5 | Integration | Connect all services | `docker compose up` |

---

## Quick References

| Resource | Location |
|----------|----------|
| **Quick Install Guide** | [QUICK_INSTALL.md](../QUICK_INSTALL.md) |
| **Task Checklist** | [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) |
| **Daily Progress** | [DAILY_LOG.md](DAILY_LOG.md) |
| **API Contracts** | [PROJECT_PLAN.md](../PROJECT_PLAN.md#api-contracts) |
| **Risk Assessment** | [PROJECT_PLAN.md](../PROJECT_PLAN.md#risk-assessment) |
| **Technology Stack** | [TECHNOLOGY_RECOMMENDATIONS.md](../TECHNOLOGY_RECOMMENDATIONS.md) |
| **Architecture Diagrams** | [architecture_diagrams.md](../architecture_diagrams.md) |

## Service Ports

| Service | Host Port | Internal Port |
|---------|-----------|---------------|
| Orchestrator API | 5100 | 8000 |
| PPTX Generator | 5101 | 8001 |
| Frontend | 5102 | 80 |
| Ollama | (external) | 11434 |

> Ports configurable via `.env` file. See [QUICK_INSTALL.md](../QUICK_INSTALL.md) for details.

---

## Success Criteria

Sprint 1 is complete when:
- [x] User can input presentation topic via web interface
- [x] System processes input and generates PPTX (supports 3-20 slides)
- [x] User can download generated PPTX file
- [x] All components run in Docker containers
- [x] Basic error handling is implemented
- [x] Health endpoints are available on all services
- [x] **BONUS:** Guided Mode with AI-assisted conversation

**Quality Targets:**
- ✅ PPTX generation < 1 second
- ✅ Docker image sizes < 200MB each
- ✅ Code follows clean code principles
