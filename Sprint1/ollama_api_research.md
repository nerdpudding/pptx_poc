# Ollama API Research

> **Datum:** 2025-12-04
> **Doel:** Documentatie van Ollama API parameters voor PPTX POC project

---

## Bronnen

| Bron | URL | Beschrijving |
|------|-----|--------------|
| Ollama API Docs | https://docs.ollama.com/api/introduction | Officiële API introductie |
| Ollama Modelfile | https://docs.ollama.com/modelfile | Parameter referentie voor Modelfiles |
| Ollama GitHub API | https://github.com/ollama/ollama/blob/main/docs/api.md | Gedetailleerde API documentatie |
| Ollama Python Client | https://github.com/ollama/ollama-python | Python library met streaming voorbeelden |

---

## API Endpoints

### Belangrijkste Endpoints

| Endpoint | Method | Beschrijving |
|----------|--------|--------------|
| `/api/generate` | POST | Genereer response voor prompt |
| `/api/chat` | POST | Chat conversation (multi-turn) |
| `/api/embed` | POST | Vector embeddings genereren |
| `/api/tags` | GET | Lijst van beschikbare models |
| `/api/ps` | GET | Actief draaiende models |
| `/api/show` | POST | Model details opvragen |
| `/api/pull` | POST | Model downloaden |
| `/api/version` | GET | Ollama versie |

### Base URL
- **Lokaal:** `http://localhost:11434/api`
- **Docker network:** `http://ollama:11434/api`

---

## /api/generate - Request Parameters

### Top-Level Parameters

| Parameter | Type | Required | Default | Beschrijving |
|-----------|------|----------|---------|--------------|
| `model` | string | **Ja** | - | Model naam (bijv. `llama3.2`, `ministral-3-14b-it-2512-q8-120k:latest`) |
| `prompt` | string | Ja | - | Input tekst voor generatie |
| `system` | string | Nee | Modelfile | **System message** - overschrijft Modelfile SYSTEM |
| `template` | string | Nee | Modelfile | Prompt template override |
| `format` | string/object | Nee | - | `"json"` voor JSON mode, of JSON schema object |
| `stream` | bool | Nee | `true` | Streaming aan/uit |
| `raw` | bool | Nee | `false` | Skip prompt formatting |
| `keep_alive` | string | Nee | `"5m"` | Hoe lang model in VRAM blijft |
| `suffix` | string | Nee | - | Tekst na model response (voor code completion) |
| `images` | array | Nee | - | Base64 images voor multimodal models |
| `context` | array | Nee | - | **Deprecated** - conversation context |

### Options Object

Alle generatie parameters gaan in het `options` object:

```json
{
  "model": "ministral-3-14b-it-2512-q8-120k:latest",
  "prompt": "...",
  "format": "json",
  "stream": false,
  "options": {
    "temperature": 0.15,
    "num_ctx": 122880,
    "num_predict": 2048,
    "top_k": 40,
    "top_p": 0.9
  }
}
```

---

## Options Parameters (Volledig)

### Sampling Parameters

| Parameter | Type | Default | Range | Beschrijving |
|-----------|------|---------|-------|--------------|
| `temperature` | float | 0.8 | 0.0 - 2.0 | Creativiteit/randomness. Lager = meer deterministisch, hoger = creatiever |
| `top_k` | int | 40 | 1 - 100 | Aantal token kandidaten om uit te kiezen. Hoger = meer divers |
| `top_p` | float | 0.9 | 0.0 - 1.0 | Nucleus sampling. Cumulatieve probability threshold |
| `min_p` | float | 0.0 | 0.0 - 1.0 | Alternatief voor top_p. Minimum probability relatief aan top token |
| `seed` | int | 0 | - | Random seed voor reproduceerbare output |

### Output Control

| Parameter | Type | Default | Beschrijving |
|-----------|------|---------|--------------|
| `num_predict` | int | -1 | Max tokens te genereren. `-1` = infinite, `-2` = fill context |
| `stop` | array | - | Stop sequences. Generatie stopt bij deze patterns |

### Context & Memory

| Parameter | Type | Default | Beschrijving |
|-----------|------|---------|--------------|
| `num_ctx` | int | 2048 | Context window size. Hoeveel tokens model kan "zien" |
| `repeat_last_n` | int | 64 | Hoeveel tokens terug te kijken voor herhaling detectie. `0` = disabled, `-1` = num_ctx |
| `repeat_penalty` | float | 1.1 | Penalty voor herhaalde tokens. Hoger = strenger |

### Geavanceerde Parameters

| Parameter | Type | Default | Beschrijving |
|-----------|------|---------|--------------|
| `mirostat` | int | 0 | Mirostat sampling mode (0 = disabled, 1 = Mirostat, 2 = Mirostat 2.0) |
| `mirostat_eta` | float | 0.1 | Learning rate voor Mirostat |
| `mirostat_tau` | float | 5.0 | Target entropy voor Mirostat |
| `tfs_z` | float | 1.0 | Tail free sampling parameter |
| `num_gpu` | int | - | Aantal GPU layers (voor offloading) |
| `num_thread` | int | - | Aantal CPU threads |
| `num_batch` | int | 512 | Batch size voor prompt processing |

---

## Response Format

### Streaming Response (default)

Meerdere JSON objecten, elk met:

```json
{
  "model": "ministral-3-14b-it-2512-q8-120k:latest",
  "created_at": "2025-12-04T10:30:00.000Z",
  "response": "token text here",
  "done": false
}
```

### Final Response (laatste object of non-streaming)

```json
{
  "model": "ministral-3-14b-it-2512-q8-120k:latest",
  "created_at": "2025-12-04T10:30:05.000Z",
  "response": "complete text if non-streaming",
  "done": true,
  "done_reason": "stop",
  "context": [1, 2, 3, ...],
  "total_duration": 5000000000,
  "load_duration": 1000000000,
  "prompt_eval_count": 50,
  "prompt_eval_duration": 500000000,
  "eval_count": 200,
  "eval_duration": 3500000000
}
```

### Timing Metrics

| Field | Beschrijving |
|-------|--------------|
| `total_duration` | Totale tijd in nanoseconden |
| `load_duration` | Model load tijd |
| `prompt_eval_count` | Aantal prompt tokens |
| `prompt_eval_duration` | Prompt verwerking tijd |
| `eval_count` | Aantal gegenereerde tokens |
| `eval_duration` | Generatie tijd |

---

## JSON Mode & Structured Output

### Simple JSON Mode

```json
{
  "model": "ministral-3-14b-it-2512-q8-120k:latest",
  "prompt": "Return a JSON object with name and age",
  "format": "json",
  "stream": false
}
```

**Belangrijk:** Instrueer het model in de prompt om JSON te gebruiken, anders kan het excessieve whitespace genereren.

### JSON Schema Mode

```json
{
  "model": "ministral-3-14b-it-2512-q8-120k:latest",
  "prompt": "Generate a person",
  "format": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "age": {"type": "integer"}
    },
    "required": ["name", "age"]
  },
  "stream": false
}
```

---

## Streaming met Python

### Sync Streaming

```python
from ollama import generate

stream = generate(
    model='ministral-3-14b-it-2512-q8-120k:latest',
    prompt='Why is the sky blue?',
    stream=True
)

for chunk in stream:
    print(chunk['response'], end='', flush=True)
```

### Async Streaming

```python
import asyncio
from ollama import AsyncClient

async def stream_generate():
    async for part in await AsyncClient().generate(
        model='ministral-3-14b-it-2512-q8-120k:latest',
        prompt='Why is the sky blue?',
        stream=True
    ):
        print(part['response'], end='', flush=True)

asyncio.run(stream_generate())
```

### Raw HTTP Streaming (httpx)

```python
import httpx

async def stream_ollama():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            'POST',
            'http://ollama:11434/api/generate',
            json={
                'model': 'ministral-3-14b-it-2512-q8-120k:latest',
                'prompt': 'Hello',
                'stream': True
            }
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    print(data['response'], end='', flush=True)
```

---

## Aanbevolen Settings voor PPTX POC

### Productie (consistente JSON output)

```json
{
  "options": {
    "temperature": 0.15,
    "num_ctx": 122880,
    "num_predict": 4096,
    "top_k": 40,
    "top_p": 0.9,
    "repeat_penalty": 1.1
  }
}
```

### Debug/Test (snellere response)

```json
{
  "options": {
    "temperature": 0.15,
    "num_ctx": 8192,
    "num_predict": 1024,
    "top_k": 40,
    "top_p": 0.9
  }
}
```

---

## Context Size Opties

Voor frontend slider:

| Label | Value | Use Case |
|-------|-------|----------|
| 4K | 4096 | Snelle tests |
| 8K | 8192 | Korte prompts |
| 16K | 16384 | Standaard |
| 32K | 32768 | Langere context |
| 64K | 65536 | Uitgebreide context |
| 100K | 102400 | Large context |
| 120K | 122880 | Model default (onze GPU) |
| 128K | 131072 | Near maximum |
| 170K | 174080 | Extended |
| 200K | 204800 | Very large |
| 256K | 262144 | Maximum (model afhankelijk) |

**Let op:** Hogere context = meer VRAM gebruik. Test wat je GPU aankan.

---

## Implementatie Notities

### Voor PPTX POC

1. **`format: "json"`** is essentieel voor betrouwbare JSON output
2. **`system`** parameter gebruiken voor prompt template in plaats van in prompt zelf
3. **Streaming** implementeren voor betere UX (live feedback)
4. **`num_predict`** beperken voorkomt runaway generation
5. **Timeouts** in nginx verhogen naar 180s+ voor grote models

### Frontend Settings Menu

Parameters om exposed te maken:
- `temperature` (slider 0.0 - 2.0)
- `num_ctx` (dropdown met presets)
- `num_predict` (slider of input)
- `top_k` (slider 1 - 100)
- `top_p` (slider 0.0 - 1.0)
- `system` (textarea voor system prompt)

---

*Laatste update: 2025-12-04*
