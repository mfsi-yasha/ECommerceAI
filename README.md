# E-Commerce AI System

A scalable, production-grade, RAG (Retrieval-Augmented Generation) e-commerce assistant. This project utilizes a microservices architecture to ensure high availability, fault tolerance, and independent scalability of AI inference, retrieval, and gateway services.

## 🏗️ System Architecture

![System Design Diagram](./docs/ECommerceAISystemDesign.jpg)

This system decouples the UI, API Gateway, and AI logic to prevent bottlenecks. The API Gateway manages session logging and traffic, while the dedicated RAG Engine (Phase 2) will manage context retrieval and orchestration.

### Current Core Components (Phase 1)
1. **Nginx:** Reverse Proxy for load balancing and routing (ports 80).
2. **Frontend (Gradio 5+):** The modern Chat UI (`/frontend`).
3. **Backend (FastAPI):** API Gateway handling session validation, logging, and routing (`/backend`).
4. **PostgreSQL 17:** Persistent storage for product metadata and chat logs.

### Upcoming Components (Phase 2)
5. **RAG Engine:** LangGraph orchestrator for context retrieval and prompt construction.
6. **Qdrant:** High-performance Vector Database for semantic search.
7. **vLLM:** GPU-optimized inference engine for LLM text generation.

---

## 📂 Project Structure

The project is organized into modular containers to support independent scaling and deployment.

```text
ECommerceAI/
├── docker-compose.yml        # Orchestration for the stack
├── Makefile                  # Helper commands for local development
├── frontend/                 # Gradio Chat UI Service
├── backend/                  # FastAPI Gateway Service (Auth/Logging/Routing)
├── nginx/                    # Nginx Configuration
└── docs/                     # Architectural documentation
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker & Docker Compose**
- **Python 3.12+** (For running local commands/tests)
- **Poetry** (For dependency management)

### Helper Commands (Makefile)

We use a `Makefile` to simplify local development and deployment. 

```bash
# Spin up the entire Docker stack in detached mode
make up

# Spin down the Docker stack (preserves database volumes)
make down

# Rebuild the Docker containers from scratch
make build

# Run the test suite in the backend
make test

# Manually trigger Alembic migrations (runs automatically on boot)
make migrate

# Seed the Postgres database with 20 mock products
make seed
```

### Initial Setup & Deployment

1. **Start the containers:**
   ```bash
   make up
   ```
   *Note: The backend container automatically runs database migrations (`alembic upgrade head`) on startup.*

2. **Seed the database (Optional but recommended):**
   ```bash
   make seed
   ```

3. **Access the Application:**
   - **Frontend UI:** [http://localhost](http://localhost)
   - **Backend API Docs:** [http://localhost/api/docs](http://localhost/api/docs)

---

## 🗄️ Database Schema

![ER Diagram](./docs/ERDiagram.jpg)

The schema is managed via **Alembic** migrations and **SQLAlchemy** ORM models located in `backend/app/models.py`.

- **Products:** Catalog storage with auto-increment IDs.
- **Product Metadata:** Separated for efficient RAG lookups.
- **Chat History:** Partitioned for context window retrieval.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python 3.12), SQLAlchemy, Alembic
- **Dependency Management:** Poetry
- **Frontend:** Gradio 5+
- **Database:** PostgreSQL 17
- **Infrastructure:** Docker, Nginx, Make
