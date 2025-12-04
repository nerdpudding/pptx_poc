# Technology Recommendations

> Research findings for Sprint 1 implementation decisions (December 2025)

---

## Summary

| Component | Technology | Why |
|-----------|------------|-----|
| Frontend | nginx:alpine + vanilla HTML/JS | KISS, tiny (~40MB), no build step |
| Orchestrator | FastAPI (Python) | Async, same lang as pptx, great Ollama support |
| PPTX Generator | python-pptx | Stable v1.0.0, standard choice |
| Ollama | ollama/ollama official image | Just works |
| LangChain | Skip for MVP | Add in Sprint 2+ if needed |

---

## 1. Frontend Container

### Recommendation: `nginx:alpine` with static HTML/CSS/JS

| Option | Size | Complexity | Fit |
|--------|------|------------|-----|
| **nginx:alpine** | ~40MB | Very Low | Best for KISS approach |
| flashspys/nginx-static | ~4MB | Low | If size is critical |
| BusyBox httpd | ~154KB | Medium | Minimal but less features |

For a simple form + download UI, plain HTML/CSS/JS served by nginx is perfect. No framework needed.

### Example Dockerfile
```dockerfile
FROM nginx:alpine
COPY ./static /usr/share/nginx/html
EXPOSE 80
```

### Sources
- [Official nginx Docker usage](https://www.docker.com/blog/how-to-use-the-official-nginx-docker-image/)
- [Lightweight nginx-static Docker image](https://github.com/docker-nginx-static/docker-nginx-static)

---

## 2. Orchestrator Container

### Recommendation: FastAPI (Python)

| Option | Pros | Cons |
|--------|------|------|
| **FastAPI** | Async, minimal boilerplate, excellent Ollama integration | Python required |
| Express.js | Familiar to JS devs | Mixing Node + Python adds complexity |
| Flask | Simple | No native async support |

### Why FastAPI?
- Native async for LLM calls (important for 30s timeout requirement)
- Same language as PPTX generator (can combine containers later)
- Well-documented Ollama integration patterns
- Auto-generates OpenAPI docs at `/docs`
- Lightweight and fast

### Example Ollama Integration
```python
from fastapi import FastAPI
import httpx

app = FastAPI()

@app.post("/api/v1/generate")
async def generate(request: GenerateRequest):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://ollama:11434/api/generate",
            json={
                "model": "ministral-3-14b-it-2512",
                "prompt": build_prompt(request.topic),
                "format": "json"
            }
        )
    return process_response(response.json())
```

### Sources
- [FastAPI + Ollama Docker example](https://github.com/bitfumes/ollama-docker-fastapi)
- [Ollama Project (FastAPI + Streamlit)](https://github.com/abcomputersatl/ollama-project)

---

## 3. PPTX Generator Container

### Recommendation: python-pptx library

| Option | Status | Notes |
|--------|--------|-------|
| **python-pptx** | v1.0.0 stable | The standard, well-maintained |
| cogniverse/pptx-genai | Docker image | Pre-built but less control |
| GemBox.Presentation | .NET only | Not applicable |

### Why python-pptx?
- Mature library (v1.0.0 released)
- No PowerPoint installation required
- Works perfectly in Docker/Linux
- Simple API for 3-slide structure
- Active maintenance

### Example Usage
```python
from pptx import Presentation
from pptx.util import Inches, Pt

def create_presentation(slides_data):
    prs = Presentation()

    for slide_data in slides_data:
        if slide_data["type"] == "title":
            layout = prs.slide_layouts[0]  # Title slide
            slide = prs.slides.add_slide(layout)
            slide.shapes.title.text = slide_data["heading"]
        elif slide_data["type"] == "content":
            layout = prs.slide_layouts[1]  # Title + Content
            slide = prs.slides.add_slide(layout)
            slide.shapes.title.text = slide_data["heading"]
            # Add bullets...

    return prs
```

### Sources
- [python-pptx Documentation](https://python-pptx.readthedocs.io/)
- [python-pptx on PyPI](https://pypi.org/project/python-pptx/)
- [python-pptx GitHub](https://github.com/scanny/python-pptx)

---

## 4. LangChain Decision

### Recommendation: Skip for MVP

| Approach | Pros | Cons |
|----------|------|------|
| **Direct Ollama HTTP** | Simple, no extra dependency | Manual prompt handling |
| LangChain | Structured prompts, chains | Overkill for single LLM call |

### Rationale
For this POC (single prompt → structured JSON response), direct HTTP calls to Ollama are simpler and sufficient. LangChain adds value when you have:
- Complex prompt chains
- RAG (Retrieval-Augmented Generation)
- Multiple model orchestration
- Agent-based workflows

Consider adding LangChain in Sprint 2+ if the orchestration becomes more complex.

### Sources
- [Docker GenAI Stack (LangChain example)](https://github.com/docker/genai-stack)
- [Ollama + LangChain ChatBot](https://abvijaykumar.medium.com/ollama-build-a-chatbot-with-langchain-ollama-deploy-on-docker-5dfcfd140363)

---

## 5. Actual docker-compose.yml

> **Note:** We use an external Ollama network to share an existing Ollama container (avoids model duplication). Ports are in the 5xxx range to avoid conflicts.

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "${FRONTEND_PORT:-5102}:80"
    depends_on:
      - orchestrator
    networks:
      - default
      - ollama-network

  orchestrator:
    build: ./orchestrator
    ports:
      - "${ORCHESTRATOR_PORT:-5100}:8000"
    environment:
      - OLLAMA_HOST=${OLLAMA_HOST:-http://ollama:11434}
      - OLLAMA_MODEL=${OLLAMA_MODEL:-ministral-3:14b-instruct-2512-q8_0}
      - PPTX_GENERATOR_URL=http://pptx-generator:8001
    networks:
      - default
      - ollama-network

  pptx-generator:
    build: ./pptx-generator
    ports:
      - "${PPTX_GENERATOR_PORT:-5101}:8001"
    networks:
      - default

networks:
  ollama-network:
    external: true
    name: ${OLLAMA_NETWORK:-ollama-network}
```

> **Ollama Setup:** See [QUICK_INSTALL.md](QUICK_INSTALL.md) for connecting to existing Ollama or fresh install.

---

## 6. Actual Project Structure

```
pptx_poc/
├── docker-compose.yml          # Main stack (external Ollama network)
├── docker-compose.ollama.yml   # Optional: standalone Ollama for fresh installs
├── .env.example                # Environment template (ports, model)
├── QUICK_INSTALL.md            # Setup guide with model recommendations
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf              # API proxy + static serving
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── app.js
├── orchestrator/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI app (slim, CORS, exception handlers)
│   ├── config.py               # pydantic-settings configuration
│   └── api/
│       ├── __init__.py
│       ├── models.py           # Pydantic request/response models
│       ├── routes.py           # API endpoints
│       └── ollama_client.py    # (pending) Async Ollama HTTP client
├── pptx-generator/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── generator.py            # FastAPI app with proper models
│   └── templates/              # (pending) Slide templates
└── Sprint1/
    ├── SPRINT1_PLAN.md
    ├── IMPLEMENTATION_CHECKLIST.md
    └── DAILY_LOG.md
```

---

## 7. Key Dependencies

### Orchestrator (requirements.txt)
```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
httpx>=0.28.0
pydantic>=2.10.0
pydantic-settings>=2.6.0
```

### PPTX Generator (requirements.txt)
```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
python-pptx>=1.0.2
pydantic>=2.10.0
```

---

## 8. Consolidation Option

Since both orchestrator and pptx-generator use Python/FastAPI, you could combine them into a single container for the MVP:

| Approach | Pros | Cons |
|----------|------|------|
| Separate containers | Clean separation, independent scaling | More complexity |
| **Combined for MVP** | Simpler, fewer moving parts | Less separation |

For Sprint 1, starting with a combined orchestrator+generator may be simpler. Split in Sprint 2 if needed.

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend framework | None (vanilla) | KISS, simple form only |
| Backend framework | FastAPI | Async, Python ecosystem |
| PPTX library | python-pptx | Stable, standard |
| LangChain | Skip for MVP | Overkill for simple use case |
| Container count | 3 + external Ollama | Frontend, Orchestrator, PPTX-Generator (Ollama external) |
| Ollama integration | External network | Avoids model duplication, shares existing Ollama |
| Port range | 5xxx | Avoids conflicts with common services |
| Orchestrator structure | SOLID | config.py, api/models.py, api/routes.py, main.py |
| Frontend files | Separated | index.html, style.css, app.js for maintainability |
