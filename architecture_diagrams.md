# Architecture Diagrams (Dark Theme Optimized - Fixed)

## System Architecture

```mermaid
graph TD
    A[User] -->|HTTP| B[Frontend Web App]
    B -->|API| C[Orchestrator Service]
    C -->|LLM Request| D[Ollama Backend\nministral-3-14b-it-2512]
    D -->|Structured Response| C
    C -->|Generation Request| E[PPTX Generator]
    E -->|PPTX File| B
    B -->|Download| A

    style A fill:#e6f3ff,stroke:#fff,color:#000
    style B fill:#4a6baf,stroke:#fff,color:#fff
    style C fill:#af4a4a,stroke:#fff,color:#fff
    style D fill:#4aaf6b,stroke:#fff,color:#fff
    style E fill:#af8a4a,stroke:#fff,color:#fff
```

## Docker Container Architecture

```mermaid
graph TD
    subgraph Docker Network [pptx-poc-network]
        A[Frontend Container\nPort: 3000] -->|HTTP| B[Orchestrator Container\nPort: 5000]
        B -->|HTTP:11434| C[Ollama Container\nministral-3-14b-it-2512\nPort: 11434]
        B -->|Internal API| D[PPTX Generator Container\nPort: 5001]
    end

    User[User Browser] -->|HTTP| A
    C -->|Model Files| Volume1[(Docker Volume: ollama-models)]
    D -->|Generated Files| Volume2[(Docker Volume: pptx-output)]

    style User fill:#e6f3ff,stroke:#fff,color:#000
    style A fill:#4a6baf,stroke:#fff,color:#fff
    style B fill:#af4a4a,stroke:#fff,color:#fff
    style C fill:#4aaf6b,stroke:#fff,color:#fff
    style D fill:#af8a4a,stroke:#fff,color:#fff
    style Volume1 fill:#333,stroke:#fff,color:#fff
    style Volume2 fill:#333,stroke:#fff,color:#fff
```

## Data Flow Diagram

```mermaid
graph LR
    subgraph Frontend
        Input[User Input Form] -->|Submit| API[API Client]
    end

    subgraph Orchestrator
        API -->|POST /generate| Endpoint[API Endpoint]
        Endpoint -->|Validate| Validator[Input Validator]
        Validator -->|Process| OllamaClient[Ollama Client]
        OllamaClient -->|Receive| ResponseParser[Response Parser]
        ResponseParser -->|Format| PPTXRequest[PPTX Request]
    end

    subgraph Ollama
        PPTXRequest -->|LLM Prompt| Model[ministral-3-14b-it-2512]
        Model -->|JSON Response| OllamaClient
    end

    subgraph PPTX Generator
        PPTXRequest -->|Slide Data| Generator[PPTX Generator]
        Generator -->|Binary| FileStorage[Temp Storage]
        FileStorage -->|File Path| Endpoint
    end

    Endpoint -->|Download URL| API
    API -->|Display Preview| Preview[Presentation Preview]
    Preview -->|Download Button| Download[File Download]

    style Input fill:#4a6baf,stroke:#fff,color:#fff
    style API fill:#4a6baf,stroke:#fff,color:#fff
    style Endpoint fill:#af4a4a,stroke:#fff,color:#fff
    style Validator fill:#af4a4a,stroke:#fff,color:#fff
    style OllamaClient fill:#af4a4a,stroke:#fff,color:#fff
    style ResponseParser fill:#af4a4a,stroke:#fff,color:#fff
    style PPTXRequest fill:#af4a4a,stroke:#fff,color:#fff
    style Model fill:#4aaf6b,stroke:#fff,color:#fff
    style Generator fill:#af8a4a,stroke:#fff,color:#fff
    style FileStorage fill:#af8a4a,stroke:#fff,color:#fff
    style Preview fill:#4a6baf,stroke:#fff,color:#fff
    style Download fill:#4a6baf,stroke:#fff,color:#fff
```

## Component Interaction Sequence

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Orchestrator
    participant Ollama
    participant PPTXGen

    User->>Frontend: Enters presentation topic
    User->>Frontend: Clicks "Generate"
    Frontend->>Orchestrator: POST /generate {topic: "..."}
    Orchestrator->>Orchestrator: Validate input
    Orchestrator->>Ollama: Send LLM prompt
    Ollama->>Ollama: Process with ministral-3-14b-it-2512
    Ollama->>Orchestrator: Return structured JSON
    Orchestrator->>Orchestrator: Parse response
    Orchestrator->>PPTXGen: POST /create {slides: [...]}
    PPTXGen->>PPTXGen: Generate PPTX file
    PPTXGen->>Orchestrator: Return file path
    Orchestrator->>Frontend: Return download URL
    Frontend->>User: Display preview
    User->>Frontend: Clicks "Download"
    Frontend->>Orchestrator: GET /download/{fileId}
    Orchestrator->>User: Return PPTX file
```

## Docker Compose Service Relationships

```mermaid
graph TD
    subgraph Services
        frontend[frontend\n- Nginx/Node.js\n- Port 3000\n- Depends: orchestrator]
        orchestrator[orchestrator\n- Node.js/Python\n- Port 5000\n- Depends: ollama, pptx-gen]
        ollama[ollama\n- ministral-3-14b-it-2512\n- Port 11434\n- Volumes: models]
        pptx-gen[pptx-generator\n- Python\n- Port 5001\n- Volumes: output]
    end

    subgraph Volumes
        models[ollama-models\n- Persistent model storage]
        output[pptx-output\n- Temporary file storage]
    end

    subgraph Network
        network[pptx-poc-network\n- Isolated container network]
    end

    frontend -->|HTTP| orchestrator
    orchestrator -->|HTTP| ollama
    orchestrator -->|HTTP| pptx-gen
    ollama -->|Volume| models
    pptx-gen -->|Volume| output
    frontend -->|Network| network
    orchestrator -->|Network| network
    ollama -->|Network| network
    pptx-gen -->|Network| network

    style frontend fill:#4a6baf,stroke:#fff,color:#fff
    style orchestrator fill:#af4a4a,stroke:#fff,color:#fff
    style ollama fill:#4aaf6b,stroke:#fff,color:#fff
    style pptx-gen fill:#af8a4a,stroke:#fff,color:#fff
    style models fill:#333,stroke:#fff,color:#fff
    style output fill:#333,stroke:#fff,color:#fff
    style network fill:#222,stroke:#fff,color:#fff
```

## Simple Overview Diagram (Dark Theme)

```mermaid
graph LR
    User -->|Browser| Frontend
    Frontend -->|API Call| Orchestrator
    Orchestrator -->|LLM Request| Ollama
    Orchestrator -->|PPTX Request| Generator
    Ollama -->|Response| Orchestrator
    Generator -->|PPTX File| Orchestrator
    Orchestrator -->|Download| Frontend
    Frontend -->|PPTX| User

    style User fill:#e6f3ff,stroke:#fff,color:#000
    style Frontend fill:#4a6baf,stroke:#fff,color:#fff
    style Orchestrator fill:#af4a4a,stroke:#fff,color:#fff
    style Ollama fill:#4aaf6b,stroke:#fff,color:#fff
    style Generator fill:#af8a4a,stroke:#fff,color:#fff
```

## Key for Dark Theme Colors
- **Light Blue (#e6f3ff):** User interactions (readable on dark themes)
- **Blue (#4a6baf):** Frontend components
- **Red (#af4a4a):** Orchestrator services
- **Green (#4aaf6b):** AI/Ollama components
- **Orange (#af8a4a):** Generator services
- **Dark (#333/#222):** Storage/volumes/network