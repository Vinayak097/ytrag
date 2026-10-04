import json
import os
from pathlib import Path

import httpx

CHUNKS_DIR = Path("chunks")
EMBEDDINGS_DIR = Path("embeddings")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8001").rstrip("/")
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "service").lower()
EMBEDDING_TIMEOUT_SECONDS = float(os.getenv("EMBEDDING_TIMEOUT_SECONDS", "60"))
MODEL_NAME = "BAAI/bge-m3"


def create_embeddings(chunks):
    texts = [chunk["text"] for chunk in chunks]
    if EMBEDDING_BACKEND == "local":
        # Keep local model loading opt-in for development/indexing only.
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(MODEL_NAME)
        return model.encode(texts, batch_size=16, show_progress_bar=True,
                            normalize_embeddings=True)
    if EMBEDDING_BACKEND != "service":
        raise ValueError("EMBEDDING_BACKEND must be 'service' or 'local'")

    vectors = []
    with httpx.Client(timeout=EMBEDDING_TIMEOUT_SECONDS) as client:
        for text in texts:
            response = client.post(f"{EMBEDDING_SERVICE_URL}/embed", json={"text": text})
            response.raise_for_status()
            embedding = response.json().get("embedding")
            if (not isinstance(embedding, list) or len(embedding) != 1024
                    or any(not isinstance(value, (int, float)) for value in embedding)):
                raise ValueError("Embedding service returned an invalid 1024-dimensional vector")
            vectors.append(embedding)
    return vectors


def process_chunks():
    EMBEDDINGS_DIR.mkdir(exist_ok=True)
    chunk_files = list(CHUNKS_DIR.glob("*.json"))
    print(f"Found {len(chunk_files)} chunk files.")

    for chunk_file in chunk_files:
        print(f"\nProcessing: {chunk_file.name}")
        with open(chunk_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        video_id = data["videoId"]
        output_file = EMBEDDINGS_DIR / f"{video_id}.json"
        if output_file.exists():
            print(f"{video_id} embeddings already exist. Skipping.")
            continue

        chunks = data["chunks"]
        print(f"Creating embeddings for {len(chunks)} chunks...")
        embeddings = create_embeddings(chunks)
        embedded_chunks = [
            {**{key: chunk[key] for key in ("videoId", "start", "end", "text")},
             "embedding": embedding.tolist() if hasattr(embedding, "tolist") else embedding}
            for chunk, embedding in zip(chunks, embeddings)
        ]
        output_data = {
            "videoId": video_id,
            "language": data.get("language"),
            "language_code": data.get("language_code"),
            "is_generated": data.get("is_generated"),
            "chunks": embedded_chunks,
            "channel": data["channel"],
        }
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(output_data, file, indent=2, ensure_ascii=False)
        print(f"Saved: {output_file}")
