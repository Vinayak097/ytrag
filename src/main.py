import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

load_dotenv()

COLLECTION_NAME = "youtube_rag"
MODEL_NAME = "BAAI/bge-m3"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = SentenceTransformer(MODEL_NAME)
    app.state.qdrant = QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
    )
    yield


app = FastAPI(lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


@app.post("/ask")
def ask(request: AskRequest):
    vector = app.state.model.encode(
        request.question,
        normalize_embeddings=True,
    ).tolist()

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
