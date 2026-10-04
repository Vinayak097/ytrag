import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

load_dotenv()

COLLECTION_NAME = "youtube_rag"
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8001").rstrip("/")
EMBEDDING_TIMEOUT_SECONDS = float(os.getenv("EMBEDDING_TIMEOUT_SECONDS", "60"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.embedding_client = httpx.Client(timeout=EMBEDDING_TIMEOUT_SECONDS)
    app.state.qdrant = QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
    )
    yield
    app.state.embedding_client.close()


app = FastAPI(lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


@app.post("/ask")
def ask(request: AskRequest):
    try:
        response = app.state.embedding_client.post(
            f"{EMBEDDING_SERVICE_URL}/embed", json={"text": request.question}
        )
        response.raise_for_status()
        body = response.json()
        vector = body.get("embedding") if isinstance(body, dict) else None
        if (not isinstance(vector, list) or len(vector) != 1024
                or any(not isinstance(value, (int, float)) for value in vector)):
            raise ValueError("Embedding service returned an invalid 1024-dimensional vector")
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="Embedding service is unavailable or timed out") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail="Embedding service returned an HTTP error") from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Embedding service returned an invalid response") from exc

    result = app.state.qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=request.limit,
        with_payload=True,
    )

    return {
        "question": request.question,
        "matches": [
            {
                "text": point.payload.get("text"),
                "url": point.payload.get("url"),
                "videoId": point.payload.get("videoId"),
                "start": point.payload.get("start"),
                "end": point.payload.get("end"),
                "score": point.score,
            }
            for point in result.points
            if point.payload
        ],
    }

@app.get("/")
def hello():
    return {
        "message":"hello"
    }
