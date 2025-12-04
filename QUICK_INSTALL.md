# Quick Install Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Configure Environment](#2-configure-environment)
  - [3. Setup Ollama](#3-setup-ollama)
  - [4. Start the Stack](#4-start-the-stack)
- [Model Selection Guide](#model-selection-guide)
- [Understanding the Ollama Network Strategy](#understanding-the-ollama-network-strategy)
- [Quick Reference](#quick-reference)

---

## Prerequisites

- Docker & Docker Compose installed
- Git installed
- NVIDIA GPU with drivers (recommended)

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd pptx_poc
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Default ports (5xxx range to avoid conflicts):

| Service | Port |
|---------|------|
| Orchestrator API | 5100 |
| PPTX Generator | 5101 |
| Frontend | 5102 |

Edit `.env` to:
- Change ports if needed
- Set `OLLAMA_MODEL` based on your GPU VRAM (see [Model Selection Guide](#model-selection-guide))

### 3. Setup Ollama

**Choose ONE option based on your situation:**

#### Option A: Fresh Install (No existing Ollama)

```bash
# Start Ollama container (creates ollama-network automatically)
# Includes GPU support and optimized KV cache settings
docker-compose -f docker-compose.ollama.yml up -d

# Pull a model (see Model Selection Guide below)
docker exec ollama ollama pull ministral-3:14b-instruct-2512-q8_0

# Update OLLAMA_MODEL in .env to match
```

**Alternative: Manual Docker Run (for more control)**

If you prefer running Ollama with specific GPU settings:

```bash
docker run -d \
  --network ollama-network \
  --gpus device=all \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  -e OLLAMA_FLASH_ATTENTION=1 \
  -e OLLAMA_KV_CACHE_TYPE=q8_0 \
  ollama/ollama
```

> **Tip:** The `OLLAMA_KV_CACHE_TYPE=q8_0` setting saves significant VRAM!

#### Option B: Use Existing Ollama Container

If you already have Ollama running with models:

```bash
# Create the network (if it doesn't exist)
docker network create ollama-network

# Connect your existing Ollama container to this network
docker network connect ollama-network <your-ollama-container-name>

# Update OLLAMA_MODEL in .env to match your available model
```

### 4. Start the Stack

```bash
docker-compose up -d
```

Verify all services are running:

```bash
docker-compose ps
```

---

## Model Selection Guide

The optimal model depends on your GPU VRAM. Experiment to find what works best!

| VRAM | Recommended Model | Notes |
|------|------------------|-------|
| **24GB** (RTX 3090/4090) | `ministral-3:14b-instruct-2512-q8_0` | Best quality |
| **16GB** (RTX 4080) | `ministral-3:14b-instruct-2512-q4_K_M` | Good balance |
| **8-12GB** | `ministral-3:8b-instruct-2512-q8_0` | Lighter option |
| **8-12GB** | `ministral-3:8b-instruct-2512-q4_K_M` | Even lighter |
| **4-8GB** | `ministral-3:3b-instruct-2512-q8_0` | Minimal VRAM |
| **4-8GB** | `ministral-3:3b-instruct-2512-q4_K_M` | Smallest |

**Pull your chosen model:**

```bash
docker exec ollama ollama pull ministral-3:14b-instruct-2512-q8_0
```

**Update `.env`:**

```bash
OLLAMA_MODEL=ministral-3:14b-instruct-2512-q8_0
```

---

## Understanding the Ollama Network Strategy

### Why External Network?

The main `docker-compose.yml` does **NOT** include Ollama. Instead, it connects to an external Docker network called `ollama-network`.

**Reasons:**

1. **Avoid Model Duplication** - Ollama models can be large. If you already have models pulled, you don't want a second copy.

2. **Flexibility** - Works whether you have existing Ollama or need a fresh install.

3. **Resource Sharing** - Multiple projects can share one Ollama instance.

### Current Configuration

The `.env` file contains:

```bash
OLLAMA_NETWORK=ollama-network      # Network name to connect to
OLLAMA_CONTAINER_NAME=ollama       # Container hostname for DNS resolution
OLLAMA_HOST=http://ollama:11434    # Full URL services use internally
OLLAMA_MODEL=<your-model>          # Model name (must be pulled in Ollama)
```

Services in the main stack connect to Ollama via Docker's internal DNS - they call `http://ollama:11434` which resolves within the `ollama-network`.

### Network Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    ollama-network                        │
│  ┌─────────┐                                            │
│  │ Ollama  │◄──── Internal DNS: ollama:11434            │
│  └─────────┘                                            │
│       ▲                                                 │
│       │                                                 │
│  ┌────┴────────────────────────────────────┐           │
│  │         docker-compose.yml               │           │
│  │  ┌──────────────┐  ┌────────────────┐   │           │
│  │  │ Orchestrator │  │ PPTX-Generator │   │           │
│  │  └──────────────┘  └────────────────┘   │           │
│  │  ┌──────────────┐                       │           │
│  │  │   Frontend   │                       │           │
│  │  └──────────────┘                       │           │
│  └─────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start stack | `docker-compose up -d` |
| Stop stack | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Start Ollama (fresh) | `docker-compose -f docker-compose.ollama.yml up -d` |
| Pull model | `docker exec ollama ollama pull <model-name>` |
| Check status | `docker-compose ps` |
| List models | `docker exec ollama ollama list` |

---

*Testing and troubleshooting sections coming soon.*
