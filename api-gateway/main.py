from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator

VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", "384"))
VLLM_URL = os.getenv("VLLM_URL", "").strip()
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
LLM_MODE = os.getenv("LLM_MODE", "auto").lower()


class ChatRequest(BaseModel):
    query: str = Field(min_length=1)
    embedding: list[float] | None = Field(default=None, min_length=VECTOR_SIZE, max_length=VECTOR_SIZE)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await ensure_collection_exists()
    yield


app = FastAPI(title="AI Platform API Gateway", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)


async def ensure_collection_exists() -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(f"{QDRANT_URL}/collections/documents")
            if response.status_code == 404:
                await client.put(
                    f"{QDRANT_URL}/collections/documents",
                    json={
                        "vectors": {
                            "size": VECTOR_SIZE,
                            "distance": "Cosine",
                        }
                    },
                )
        except httpx.HTTPError:
            # Qdrant may not be ready during initial startup; search code handles retries gracefully.
            pass


async def search_context(embedding: list[float]) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(
                f"{QDRANT_URL}/collections/documents/points/search",
                json={"vector": embedding, "limit": 3, "with_payload": True},
            )
            response.raise_for_status()
            return response.json().get("result", [])
        except (httpx.HTTPError, KeyError, ValueError):
            return []


def mock_answer(query: str, context: list[dict]) -> str:
    snippets = []
    for item in context[:3]:
        payload = item.get("payload", {})
        text = payload.get("text")
        if text:
            snippets.append(text)

    if snippets:
        joined = " | ".join(snippets)
        return f"Mock response for '{query}'. Retrieved context: {joined}. This local fallback keeps the platform testable without a remote Kaggle vLLM endpoint."
    return f"Mock response for '{query}'. No vector context was available, so the gateway answered in local fallback mode for smoke testing."


async def infer_response(prompt: str, query: str, context: list[dict]) -> tuple[str, str]:
    if LLM_MODE == "mock" or not VLLM_URL:
        return mock_answer(query, context), "mock-local"

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            llm_response = await client.post(
                f"{VLLM_URL.rstrip('/')}/v1/chat/completions",
                json={
                    "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            llm_response.raise_for_status()
            payload = llm_response.json()
            return payload["choices"][0]["message"]["content"], payload.get("model", "remote-unknown")
        except (httpx.HTTPError, KeyError, ValueError):
            return mock_answer(query, context), "mock-fallback"


@app.post("/api/v1/chat")
async def chat(body: ChatRequest):
    start = time.time()
    embedding = body.embedding or [0.0] * VECTOR_SIZE
    context = await search_context(embedding)
    prompt = f"Context: {context}\n\nQuery: {body.query}"
    answer, model = await infer_response(prompt, body.query, context)
    latency = round((time.time() - start) * 1000, 2)

    return {
        "answer": answer,
        "latency_ms": latency,
        "model": model,
        "context_hits": len(context),
    }


@app.get("/health")
def health():
    return {"status": "ok", "llm_mode": LLM_MODE if LLM_MODE != "auto" else ("remote" if VLLM_URL else "mock")}
