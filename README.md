# RepoMind – GraphRAG-Based AI System for Codebase Intelligence

An AI-powered developer tool for rapid codebase onboarding and exploration through natural-language Q&A, call graph visualization, and automated code health analysis.

Link : repo-mind-ten.vercel.app

## Features

- **Natural Language Q&A** — Ask questions about any repository and get context-aware answers powered by Graph-RAG
- **Graph-RAG Retrieval** — Combines FAISS vector search with call-graph traversal for deep semantic code understanding
- **Multi-Language Support** — Tree-sitter based ingestion for Python, Java, C++, JavaScript, and more
- **Call Graph Visualization** — Interactive exploration of function relationships and dependencies
- **Code Health Analysis** — Static analysis with metrics, code smells, and refactoring suggestions
- **Contributor Tracking** — Commit history, activity timelines, and per-author contribution summaries
- **Onboarding Docs** — Auto-generated structured documentation for any ingested repository

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python, FastAPI, LangChain, Groq LLM |
| Retrieval | FAISS, HuggingFace Embeddings, Graph-RAG |
| Parsing | Tree-sitter, GitPython |
| Frontend | React 18, Vite |
| Storage | Upstash Redis |

## Architecture

```
Repository URL / ZIP
        ↓
  Ingestion Pipeline (Tree-sitter)
  — Symbol extraction
  — Call graph construction
  — Dataflow analysis
  — Embedding generation
        ↓
  Knowledge Graph + FAISS Index
        ↓
  Graph-RAG Retrieval Engine
  — Vector search
  — Graph traversal
  — LLM answer generation
        ↓
  FastAPI Backend ← React Frontend
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `UPSTASH_REDIS_REST_URL` | Upstash Redis endpoint |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash Redis auth token |
| `GROQ_API_KEY` | Groq LLM API key |

## Usage

1. Paste a GitHub URL or upload a ZIP of a repository
2. Wait for ingestion to complete (symbols, graphs, embeddings are precomputed)
3. Chat with the codebase, explore call graphs, or view code health reports

## Project Structure

```
├── ingestion/        # Repository parsing and artifact generation
├── retrieval/        # Graph-RAG query engine and vector search
├── backend/          # FastAPI REST API
├── frontend/         # React + Vite web interface
├── code_health/      # Static analysis and health scoring
└── evaluation/       # Performance benchmarks
```
