import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


CHUNKS_DIR = Path("chunks")
EMBEDDINGS_DIR = Path("embeddings")

MODEL_NAME = "BAAI/bge-m3"

BATCH_SIZE = 16


# Load the model once
model = SentenceTransformer(MODEL_NAME)


def create_embeddings(chunks):

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    return embeddings


def process_chunks():

    EMBEDDINGS_DIR.mkdir(exist_ok=True)

    chunk_files = list(CHUNKS_DIR.glob("*.json"))

    print(f"Found {len(chunk_files)} chunk files.")

    for chunk_file in chunk_files:

        print(f"\nProcessing: {chunk_file.name}")

        # Read chunk file
        with open(chunk_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        video_id = data["videoId"]
        channel=data["channel"]

        # Output file
        output_file = EMBEDDINGS_DIR / f"{video_id}.json"

        # Skip if already embedded
        if output_file.exists():
            print(f"{video_id} embeddings already exist. Skipping.")
            continue

        chunks = data["chunks"]

        print(f"Creating embeddings for {len(chunks)} chunks...")

        # Create embeddings
        embeddings = create_embeddings(chunks)

        embedded_chunks = []

        for chunk, embedding in zip(chunks, embeddings):

            embedded_chunks.append({
                "videoId": chunk["videoId"],
                "start": chunk["start"],
                "end": chunk["end"],
                "text": chunk["text"],
                "embedding": embedding.tolist()
            })

        # Keep language information
        output_data = {
            "videoId": video_id,
            "language": data.get("language"),
            "language_code": data.get("language_code"),
            "is_generated": data.get("is_generated"),
            "chunks": embedded_chunks,
            "channel":channel
        }

        # Save embeddings
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                output_data,
                f,
                indent=2,
                ensure_ascii=False
            )

        print(f"Saved: {output_file}")


