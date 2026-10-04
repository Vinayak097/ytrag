import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-m3"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = SentenceTransformer(MODEL_NAME)
    yield


app = FastAPI(lifespan=lifespan)


class EmbedRequest(BaseModel):
    text: str = Field(min_length=1)


@app.post("/embed")
def embed(request: EmbedRequest):
    vector = app.state.model.encode(
        request.text, normalize_embeddings=True
    ).tolist()
    return {"embedding": vector}


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}
