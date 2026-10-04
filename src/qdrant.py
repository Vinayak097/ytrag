import json
import os
from pathlib import Path
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


# --------------------------------------------------
# Configuration
# --------------------------------------------------

EMBEDDINGS_DIR = Path("embeddings")

COLLECTION_NAME = "youtube_rag"

VECTOR_SIZE = 1024


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError(
        "QDRANT_URL or QDRANT_API_KEY is missing from .env"
    )


# --------------------------------------------------
# Connect to Qdrant
# --------------------------------------------------

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)


# --------------------------------------------------
# Create collection
# --------------------------------------------------

if not client.collection_exists(COLLECTION_NAME):

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )

    print(f"Created collection: {COLLECTION_NAME}")

else:

    print(f"Collection already exists: {COLLECTION_NAME}")


# --------------------------------------------------
# Upload embeddings
# --------------------------------------------------

def upload_embeddings():

    embedding_files = list(
        EMBEDDINGS_DIR.glob("*.json")
    )

    print(f"Found {len(embedding_files)} embedding files.")

    for embedding_file in embedding_files:

        print(f"\nProcessing: {embedding_file.name}")

        with open(
            embedding_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        video_id = data["videoId"]
        channel=data["channel"]

        chunks = data["chunks"]

        points = []

        for index, chunk in enumerate(chunks):

            point_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                f"{video_id}_{index}"
                )
            )

            youtube_url = (
                f"https://www.youtube.com/watch?v="
                f"{video_id}&t={int(chunk['start'])}s"
            )

            payload = {
                
                "videoId": video_id,
                "channel":channel,
                "start": chunk["start"],
                "end": chunk["end"],
                "text": chunk["text"],
                "language": data.get("language"),
                "language_code": data.get("language_code"),
                "is_generated": data.get("is_generated"),
                "url": youtube_url
            }

            points.append(
                PointStruct(
                    id=point_id,
                    vector=chunk["embedding"],
                    payload=payload
                )
            )

        # Upload all chunks from this video
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

        print(
            f"Uploaded {len(points)} chunks "
            f"from {video_id}"
        )


# --------------------------------------------------
# Run
# --------------------------------------------------

