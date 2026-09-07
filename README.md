# 🏗️ Construction Intelligent RAG System

An end-to-end, enterprise-grade **Retrieval-Augmented Generation (RAG)** platform specialized for construction engineering, project management, and contract compliance documents.

It automatically ingests, classifies, OCR-processes, chunks, indexes, and queries complex construction documents—including Bills of Quantities (BOQs), Requests for Information (RFIs), Method Statements (RAMS), Inspection & Test Plans (ITPs), Drawings, Contracts (FIDIC), and Daily Site Logs.

---

## 🌟 Key Features

- **Document Processing & OCR Pipeline**: Automated processing of PDFs and images using **PaddleOCR**, PyMuPDF, and image enhancement techniques for scanned technical blueprints and forms.
- **Intelligent Classification**: Automatic document categorization into construction document types (BOQs, RFIs, Contracts, RAMS, Specifications).
- **Hybrid Retrieval System**: Combines dense vector retrieval (**Qdrant Vector Database**) and sparse lexical search (**BM25**) using **Reciprocal Rank Fusion (RRF)** and **Cohere Reranking**.
- **Multi-LLM RAG Orchestration**: Flexible LLM integration supporting Google Gemini, Groq (Llama 3/3.3), Cohere, OpenRouter, and local offline models via **Ollama**.
- **Asynchronous Task Architecture**: **Celery** workers with **Redis** broker for decoupled, non-blocking background OCR, chunking, and embedding generation.
- **Modern Web Interface**: Built with **Next.js 16 (React 19)**, **TypeScript**, **Tailwind CSS**, and **TanStack Query** featuring document queue monitoring, admin controls, and interactive RAG chat.

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Python 3.12+, Django 6.0, Django REST Framework, Django Channels
- **Task Queue**: Celery 5.6+, Redis 7, Eventlet
- **OCR & Vision**: PaddleOCR, OpenCV, PyMuPDF (fitz), Pillow, python-magic
- **Vector DB & Search**: Qdrant (`qdrant-client`), Rank-BM25, Edit Distance
- **AI & RAG**: LangChain, Google Generative AI, Groq SDK, Cohere, Ollama

### Frontend
- **Framework**: Next.js 16 (App Router), React 19, TypeScript
- **Styling**: Tailwind CSS v4, Base UI, Lucide Icons, Sonner
- **State & Data Fetching**: TanStack React Query, Zustand
- **Analytics & Graphs**: Recharts

---

## 📋 Prerequisites

Ensure the following tools are installed on your machine:

1. **Python**: `^3.12` ([Download Python](https://www.python.org/downloads/))
2. **Node.js**: `^18.0` or `^20.0` ([Download Node.js](https://nodejs.org/))
3. **Docker Desktop** (or standalone Redis and PostgreSQL): ([Download Docker](https://www.docker.com/products/docker-desktop/))
4. **uv** (Recommended Python Package Manager) or `pip`:
   ```bash
   pip install uv
   ```

---

## 🚀 Setup & Installation Guide

### Step 1: Clone the Repository
```bash
git clone https://github.com/ashishjaiswal222/construction-intelligent-rag.git
cd construction-intelligent-rag
```

### Step 2: Environment Configuration
Copy the sample environment file `.env.example` to create your local `.env` file:
```bash
cp .env.example .env
```

Open `.env` and fill in your database credentials and API keys:
```env
SECRET_KEY=your-custom-django-secret-key
DATABASE_URL=postgres://postgres:1234@localhost:5432/construction_ai
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# LLM Providers (Fill at least one preferred provider)
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
COHERE_API_KEY=your_cohere_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
OLLAMA_BASE_URL=http://localhost:11434
```

### Step 3: Database & Redis Initialization

1. **Start Redis Container** (if using Docker):
   ```bash
   docker run -d --name redis-server -p 6379:6379 redis:7-alpine
   ```

2. **Create PostgreSQL Database**:
   Run the database creation helper script:
   ```bash
   python create_db.py
   ```
   *(Or create the PostgreSQL database manually named `construction_ai`)*.

### Step 4: Python Backend Setup

Using `uv` (Recommended):
```bash
uv sync
```

Or using standard `pip`:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r pyproject.toml
```

Apply Django database migrations:
```bash
uv run python manage.py migrate
```

Create a Django Superuser (Optional):
```bash
uv run python manage.py createsuperuser
```

### Step 5: Next.js Frontend Setup

Navigate into the `frontend` directory and install dependencies:
```bash
cd frontend
npm install
cd ..
```

---

## 🏃 Running the Application

### Option A: Automated One-Click Start (Windows)
Run the provided batch script to automatically spin up Redis, Celery Workers, Celery Beat, Django Backend, and the Next.js Frontend in separate windows:
```cmd
start_all.bat
```

---

### Option B: Manual Service Startup

Open separate terminal tabs/windows for each service:

1. **Redis Server**:
   ```bash
   docker start redis-server
   ```

2. **Celery Worker**:
   ```bash
   uv run celery -A core worker -l info -P eventlet -Q celery,llm_gemini_queue,llm_ollama_queue --concurrency=12
   ```

3. **Celery Beat (Task Scheduler)**:
   ```bash
   uv run celery -A core beat -l info
   ```

4. **Django Backend Server**:
   ```bash
   uv run python manage.py runserver 0.0.0.0:8000
   ```
   *Backend running at:* `http://localhost:8000`

5. **Next.js Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   *Frontend running at:* `http://localhost:3000`

---

## 📂 Repository Structure

```
construction-intelligent-rag/
├── core/                       # Django project configuration & settings
├── document_processing/        # OCR (PaddleOCR), page extraction & signal handling
├── document_classification/    # Construction doc category classification
├── document_chunking/          # Semantic & structural document chunking
├── document_indexing/          # Vector indexing (Qdrant) & BM25 sparse index
├── document_metadata/          # Structured metadata & revision management
├── document_refinement/        # Multi-region OCR & human-in-the-loop review
├── document_retrieval/         # Hybrid retrieval engine (Vector + BM25 + RRF + Cohere)
├── rag_generation/             # Multi-LLM RAG prompt engineering & pipelines
├── project_management/         # Construction projects & task queues
├── shared/                     # Shared models, utilities, and base classes
├── future_enhancement_docs/    # Architecture & future design documentation
├── scripts/                    # Utility scripts (cost modeling, CLI tools)
├── uploads/                    # Local storage for uploaded files (.gitignore protected)
├── frontend/                   # Next.js 16 / React 19 Frontend Web Application
│   ├── src/app/                # App Router pages & admin dashboards
│   ├── src/components/         # UI components & admin queue tables
│   └── src/store/              # Zustand global state management
├── create_db.py                # PostgreSQL database initializer
├── manage.py                   # Django CLI utility
├── pyproject.toml              # Python project metadata & dependencies
├── start_all.bat               # Windows all-in-one startup launcher
├── start_celery.bat            # Standalone Celery launcher
└── README.md                   # Project documentation
```

---

## 📖 Architecture & Future Docs

Additional architectural blueprints and design documents can be found in:
- [`future_enhancement_docs/`](future_enhancement_docs/)
  - `multi_region_ocr_pipeline.md`
  - `parallel_fanout_orchestration.md`
- [`document_processing/documentation/`](document_processing/documentation/)

---

## 🛡️ License

This project is released under the MIT License.