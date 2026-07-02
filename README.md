# E-Commerce AI System

A scalable, production-grade e-commerce shopping assistant powered by Retrieval-Augmented Generation (RAG). Built on a microservices architecture with independent services for the UI, API Gateway, AI orchestration, vector search, and LLM inference.

## 🏗️ System Architecture

![System Design Diagram](./docs/ECommerceAISystemDesign.jpg)

The UI, API Gateway, and AI logic are fully decoupled so each service can scale independently without creating bottlenecks. The API Gateway manages session logging and request routing, while the RAG Engine orchestrates context retrieval and AI response generation.

### Core Components (7-Container Stack)

1. **Nginx** — Reverse proxy for routing and load balancing (port 80).
2. **Frontend (Gradio 5+)** — Chat-based shopping UI.
3. **Backend (FastAPI)** — API Gateway that handles session management, request delegation, and product data hydration.
4. **PostgreSQL 17** — Persistent storage for the product catalog, metadata, and chat logs.
5. **RAG Engine** — LangGraph-based orchestrator for query understanding, semantic retrieval, ranking, and AI response generation.
6. **Qdrant** — High-performance vector database for semantic product search.
7. **Ollama** — Hardware-agnostic LLM inference engine running Microsoft Phi-3.

---

## 📂 Project Structure

```text
ECommerceAI/
├── docker-compose.yml        # Orchestration for the 7-container stack
├── Makefile                  # Helper commands for local development
├── .env                      # Environment variables (localhost defaults)
├── frontend/                 # Gradio Chat UI
├── backend/                  # FastAPI API Gateway
│   └── app/
│       ├── main.py           #   Route handlers and RAG Engine delegation
│       ├── database.py       #   SQLAlchemy engine and session factory
│       ├── models.py         #   ORM models (Product, ProductMetadata, ChatHistory)
│       ├── schemas.py        #   Pydantic request/response schemas
│       └── repositories.py   #   Database query layer
├── rag_engine/               # RAG Engine (AI Brain)
│   ├── app/
│   │   ├── main.py           #   FastAPI server exposing /rag/query
│   │   ├── config.py         #   Environment-based configuration
│   │   ├── hardware.py       #   CUDA / MPS / CPU auto-detection
│   │   ├── graph.py          #   LangGraph pipeline assembly
│   │   ├── nodes/            #   Pipeline nodes (parser, retriever, ranker, responder)
│   │   └── clients/          #   Service clients (Qdrant, Postgres, Ollama)
│   └── scripts/
│       └── sync_vectors.py   #   Syncs product data from Postgres → Qdrant
├── nginx/                    # Nginx configuration
└── docs/                     # Architecture diagrams
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker & Docker Compose**
- **Python 3.12+** (for local commands and tests)
- **Poetry** (for dependency management)

### Makefile Commands

```bash
make up              # Build and start all 7 containers
make down            # Stop all containers (preserves volumes)
make build           # Rebuild Docker images
make test            # Run the backend test suite
make migrate         # Run Alembic database migrations
make seed            # Seed the database with sample products
make sync-vectors    # Sync product vectors from Postgres to Qdrant (locally)
```

### Initial Setup

1. **Start the containers:**

   ```bash
   make up
   ```

   _The backend automatically runs database migrations on startup._

2. **Seed the database:**

   ```bash
   make seed
   ```

3. **Sync product vectors to Qdrant:**

   ```bash
   docker exec ecommerce_rag_engine python scripts/sync_vectors.py
   ```

4. **Open the application:**
   - **Chat UI:** [http://localhost](http://localhost)
   - **API Docs:** [http://localhost/api/docs](http://localhost/api/docs)

---

## 🧠 RAG Pipeline

The RAG Engine uses a 4-node [LangGraph](https://langchain-ai.github.io/langgraph/) pipeline to process every user query:

```
User Query → [Parse] → [Retrieve] → [Rank] → [Respond] → {ai_response, product_ids}
```

| Node         | What it does                                                                                                                                    |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Parse**    | Extracts structured exact-match metadata filters (brand, type, subtype, price range) from the query using the LLM                               |
| **Retrieve** | Embeds the query → searches Qdrant with exact metadata filters (strict match) and semantic scoring (0.3 threshold) → falls back to Postgres SQL |
| **Rank**     | Caps results at 10 and classifies the outcome (shortage / overflow / empty / normal)                                                            |
| **Respond**  | Drafts a conversational AI response via the LLM, with resilient JSON fallback if offline                                                        |

### Inventory & Pagination Rules

- **Default:** Maximum 10 products per response.
- **Shortage:** Fewer matches than requested — acknowledges the limited selection.
- **Overflow:** More matches than the cap — shows the top results and offers to show more.
- **Empty:** No matches — suggests broadening the search.

---

## 🗄️ Database Schema

The schema is managed with **Alembic** migrations and defined in **SQLAlchemy** ORM models ([models.py](./backend/app/models.py)).

![ER Diagram](./docs/ERDiagram.jpg)

| Table                | Purpose                                                         |
| -------------------- | --------------------------------------------------------------- |
| **products**         | Core product catalog with category type and subtype.            |
| **product_metadata** | Flexible key-value pairs (brand, price, color, specs, etc.).    |
| **chat_history**     | Conversation log keyed by UUID session ID for history playback. |

---

## ⚙️ Hardware Agnostic

The system automatically detects and uses the best available compute hardware:

| Environment            | Compute | Notes                               |
| ---------------------- | ------- | ----------------------------------- |
| NVIDIA GPU (Docker)    | CUDA    | Requires `nvidia-container-toolkit` |
| Apple Silicon (native) | MPS     | For local execution outside Docker  |
| Apple Silicon (Docker) | CPU     | Docker runs ARM64 Linux, no Metal   |
| Intel/AMD              | CPU     | Universal fallback                  |

---

## 🛠️ Tech Stack

| Layer           | Technology                                      |
| --------------- | ----------------------------------------------- |
| Frontend        | Gradio 6+                                       |
| API Gateway     | FastAPI, SQLAlchemy, Alembic                    |
| RAG Engine      | LangGraph, Sentence-Transformers, Qdrant Client |
| LLM             | Ollama (Microsoft Phi-3), OpenAI-compatible API |
| Database        | PostgreSQL 17                                   |
| Vector Database | Qdrant                                          |
| Dependencies    | Poetry                                          |
| Infrastructure  | Docker, Nginx, Make                             |

---
