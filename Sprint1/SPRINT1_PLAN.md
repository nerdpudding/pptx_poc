# Sprint 1: Implementation Plan

## Sprint Overview

**Duration:** 2-3 weeks (flexible)
**Objective:** Implement the core PowerPoint generation functionality based on Sprint 0 research and planning
**Status:** Planning Complete | Implementation Not Started

## Development Philosophy: Container-First

> **All services run in Docker containers from day one.**
> No need to install Python, Node, etc. locally - just Docker.

For each component:
1. Write the code
2. Create the Dockerfile immediately
3. Add to docker-compose.yml
4. Build and test via `docker-compose up`

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

### Phase 0: Project Setup
**Estimate:** 1 hour

Create the complete project structure upfront.

```bash
# Create all directories
mkdir -p frontend/static
mkdir -p orchestrator/api
mkdir -p pptx-generator/templates
```

**Files to Create:**
```
pptx_poc/
├── docker-compose.yml          # Create first, add services incrementally
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

### Phase 1: Backend API + Container
**Estimate:** 3-4 days

Build the orchestrator service with immediate containerization.

**Create Together:**
- `orchestrator/main.py` - FastAPI application
- `orchestrator/Dockerfile` - Container definition
- `docker-compose.yml` - Add orchestrator service

**Test:** `docker-compose up orchestrator` then curl the endpoints

### Phase 2: PPTX Generator + Container
**Estimate:** 2-3 days

Build the PPTX generator service with immediate containerization.

**Create Together:**
- `pptx-generator/generator.py` - Python-pptx service
- `pptx-generator/Dockerfile` - Container definition
- Update `docker-compose.yml` - Add pptx-generator service

**Test:** `docker-compose up pptx-generator` then test generation

### Phase 3: Frontend + Container
**Estimate:** 2-3 days

Build the frontend with immediate containerization.

**Create Together:**
- `frontend/static/index.html`, `style.css`, `app.js`
- `frontend/Dockerfile` - nginx:alpine container
- `frontend/nginx.conf` - Proxy configuration
- Update `docker-compose.yml` - Add frontend service

**Test:** `docker-compose up frontend` then test in browser

### Phase 4: Integration & Testing
**Estimate:** 1-2 days

All services running together in containers.

**Test:** `docker-compose up` - full stack testing

---

## Development Order (Docker-First)

| Step | Component | What to Create | How to Test |
|------|-----------|----------------|-------------|
| 1 | Setup | Project folders + docker-compose.yml skeleton | N/A |
| 2 | Backend | Code + Dockerfile together | `docker-compose up orchestrator` + curl |
| 3 | PPTX | Code + Dockerfile together | `docker-compose up pptx-generator` |
| 4 | Frontend | Code + Dockerfile together | `docker-compose up frontend` |
| 5 | Integration | Connect all services | `docker-compose up` |

---

## Quick References

| Resource | Location |
|----------|----------|
| **Task Checklist** | [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) |
| **Daily Progress** | [DAILY_LOG.md](DAILY_LOG.md) |
| **API Contracts** | [PROJECT_PLAN.md](../PROJECT_PLAN.md#api-contracts) |
| **Risk Assessment** | [PROJECT_PLAN.md](../PROJECT_PLAN.md#risk-assessment) |
| **Technology Stack** | [TECHNOLOGY_RECOMMENDATIONS.md](../TECHNOLOGY_RECOMMENDATIONS.md) |
| **Architecture Diagrams** | [architecture_diagrams.md](../architecture_diagrams.md) |

---

## Success Criteria

Sprint 1 is complete when:
- [ ] User can input presentation topic via web interface
- [ ] System processes input and generates 3-slide PPTX
- [ ] User can download generated PPTX file
- [ ] All components run in Docker containers
- [ ] Basic error handling is implemented
- [ ] Health endpoints are available on all services

**Quality Targets:**
- Response time < 30 seconds
- Docker image sizes < 200MB each
- Code follows clean code principles
