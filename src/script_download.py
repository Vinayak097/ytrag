urls=[
    "https://youtu.be/S8tpzqrwnHk?si=t4JXqqKA5n9OfyuR"
]
import json
from pathlib import Path
import time
from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp import YoutubeDL
import yt_dlp
TRANSCRIPT_FILE = Path("transcript.json")
TRANSCRIPT_DIR = Path("transcript")
TRANSCRIPT_DIR.mkdir(exist_ok=True)
 


from urllib.parse import urlparse, parse_qs


def get_video_id(url):

    parsed_url = urlparse(url)

    # https://www.youtube.com/watch?v=qH2VQY48mg4
    if "youtube.com" in parsed_url.netloc:
        return parse_qs(parsed_url.query)["v"][0]

    # https://youtu.be/qH2VQY48mg4?si=xxxxx
    if "youtu.be" in parsed_url.netloc:
        return parsed_url.path.strip("/")

    return None


def Transcript():
    
     for url in urls:

        # Get video ID
        video_id = get_video_id(url)
        if not video_id:
            print(f"Invalid YouTube URL: {url}")
            continue 
        print("videoId:", video_id) # File for this specific video transcript_file = TRANSCRIPT_DIR / f"{video_id}.json" # Check if transcript already exists if transcript_file.exists(): print(f"{video_id} already exists. Skipping.") continue

        try:
            # Fetch transcript
            fetched = YouTubeTranscriptApi().fetch(
                video_id,
                languages=["en-US", "en", "hi"]
            )

            # Convert to our format
            segments = []

            for item in fetched:
                segments.append({
                    "text": item.text,
                    "start": item.start,
                    "duration": item.duration
                })
            print("segmentes " , segments)
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                info = ydl.extract_info(url, download=False)

            channel = info["channel"]
            # Create video object
            new_transcript = {
                "language":fetched.language,
                "language_code":fetched.language_code,
                "is_generated":fetched.is_generated,
                "videoId": video_id,
                "channel":channel,
                "segments": segments
               
            }

            # Add to transcript array
            
            transcript_file = TRANSCRIPT_DIR / f"{video_id}.json"

            # Save immediately
            with open(transcript_file, "w", encoding="utf-8") as f:
                json.dump(
                    new_transcript,
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            print(f"Saved {video_id}")

            # Wait before next YouTube request
            for seconds in range(120, 0, -1):
                print(f"Next request in {seconds} seconds...", end="\r")
                time.sleep(1)

        except Exception as e:
            print(f"Failed for {video_id}: {e}")
            break

    



        


def prints():
    print("import works")