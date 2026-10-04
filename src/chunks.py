import json
from pathlib import Path


TRANSCRIPT_DIR = Path("transcript")
CHUNKS_DIR = Path("chunks")

CHUNK_DURATION = 60


def create_chunks(transcript):
    video_id = transcript["videoId"]
    segments = transcript["segments"]

    chunks = []

    current_text = []
    chunk_start = None
    chunk_end = None

    for segment in segments:

        start = segment["start"]
        end = start + segment["duration"]

        # Start a new chunk
        if chunk_start is None:
            chunk_start = start

        # Add this complete transcript segment
        current_text.append(segment["text"])
        chunk_end = end

        # Check if chunk reached 60 seconds
        if chunk_end - chunk_start >= CHUNK_DURATION:

            chunks.append({
                "videoId": video_id,
                "start": chunk_start,
                "end": chunk_end,
                "text": " ".join(current_text)
            })

            # Reset for next chunk
            current_text = []
            chunk_start = None
            chunk_end = None

    # Add remaining segments
    if current_text:
        chunks.append({
            "videoId": video_id,
            "start": chunk_start,
            "end": chunk_end,
            "text": " ".join(current_text)
        })

    return chunks


def process_transcripts():

    # Create chunks folder if it doesn't exist
    CHUNKS_DIR.mkdir(exist_ok=True)

    transcript_files = list(TRANSCRIPT_DIR.glob("*.json"))

    print(f"Found {len(transcript_files)} transcript files.")

    for transcript_file in transcript_files:

        print(f"\nProcessing: {transcript_file.name}")

        # Read transcript
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript = json.load(f)

        video_id = transcript["videoId"]
        channel=transcript["channel"]
        # Output file for this video
        output_file = CHUNKS_DIR / f"{video_id}.json"

        # Skip if already processed
        if output_file.exists():
            print(f"{video_id} chunks already exist. Skipping.")
            continue

        # Create chunks
        chunks = create_chunks(transcript)

        # Save chunks
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "videoId": video_id,
                    "channel":channel,
                    "chunks": chunks
                },
                f,
                indent=2,
                ensure_ascii=False
            )

        print(f"Created {len(chunks)} chunks")
        print(f"Saved: {output_file}")


