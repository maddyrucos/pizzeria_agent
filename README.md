# Pizzeria Agent

An experimental LangGraph agent that helps customers order pizza delivery or book a table for a single pizzeria location. It uses retrieval-augmented generation (RAG) over menu and review data to keep answers grounded and exposes a FastAPI backend for programmatic access.

## Features
- Guided assistant that enforces clarifying questions before calling tools when user input is incomplete.
- Tools for creating delivery orders, booking tables, and searching a knowledge base of menu items and recent reviews.
- RAG pipeline powered by SentenceTransformers embeddings and a local Chroma vector store built from the CSV data in `data/`.
- FastAPI service that maintains simple in-memory chat state per user.
- vLLM scripts to serve the `Qwen/Qwen2.5-3B-Instruct` model with OpenAI-compatible APIs and automatic tool calling.

## Repository structure
- `agent/` — LangGraph agent logic and tool implementations.
  - `main.py` — graph wiring, system prompt, and tool routing.
  - `tools.py` — delivery ordering, table booking, and knowledge base search tools.
  - `rag.py` — builds the vector store from CSV menu/review data and exposes a retriever.
- `backend/` — FastAPI app that exposes the agent at `/agent`, keeping chat histories in memory.
- `data/` — sample CSV data for the RAG corpus (menu items and restaurant reviews).
- `llm/` — Dockerfile and scripts to run the vLLM server for the Qwen model.
- `requirements.txt` — Python dependencies for the agent and backend.

## Prerequisites
- Python 3.11+ with `uvicorn` and dependencies from `requirements.txt`.
- Access to a GPU (recommended) for running the vLLM server with the Qwen model.
- Docker (optional) if you prefer to run the model server in a container.

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the model server
You can launch vLLM locally or with Docker. Both expose an OpenAI-compatible API at `http://localhost:8000/v1`.

**Local process**
```bash
bash llm/run_model.sh
```

**Docker**
```bash
# build the image (run from repository root)
docker build -t vllm-qwen llm/
# start the server
docker run -d \
  --name vllm-qwen \
  --restart unless-stopped \
  --gpus all \
  --network host \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm-qwen
```

## Running the FastAPI backend
Start the API after the model server is available:
```bash
uvicorn backend.main:app --reload --port 9000
```

The endpoint expects a JSON payload with the user ID and a list of message strings (they are appended as `HumanMessage` entries). The backend keeps an in-memory state per user.

**Example request**
```bash
curl -X POST http://localhost:9000/agent \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "message": ["Привет, есть пицца Маргарита?"]}'
```

## Notes on RAG data
The first RAG call will build a persistent Chroma database at `data/chroma_db`. It is derived from:
- `data/pizzeria_menu.csv` — menu items with categories, descriptions, and USD prices.
- `data/restaurant_reviews.csv` — recent review snippets with ratings.

If you update the CSVs, delete `data/chroma_db` to rebuild embeddings on next start.

## Local development
- The agent system prompt and tool routing live in `agent/main.py` and are a good starting point for behavior changes.
- Tool schemas and RAG logic live in `agent/tools.py` and `agent/rag.py`.
- The FastAPI app in `backend/main.py` currently stores chat state in memory; swap `CHATS` out for a database if you need persistence or scaling.

## Troubleshooting
- Ensure the model server is reachable at `http://localhost:8000/v1`. The agent binds tools to that endpoint and will fail if it cannot connect.
- If vector search returns no results after data changes, remove `data/chroma_db` and restart to rebuild the index.
- For CUDA issues when running vLLM, verify GPU drivers and CUDA runtime versions match your environment.
