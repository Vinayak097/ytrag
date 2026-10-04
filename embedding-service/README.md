# BGE-M3 embedding service

This service is the only production process that loads `BAAI/bge-m3`. It exposes `POST /embed` with `{"text":"..."}` and returns `{"embedding":[...]}`. Vectors are normalized, matching the existing indexing and search behavior. It has no CORS middleware; call it from the backend or over Render's private service network.

Run locally from this directory:

```bash
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

Deploy as a Render **Web Service** with this directory as its root, Python runtime, build command `pip install -r requirements.txt`, and start command `uvicorn main:app --host 0.0.0.0 --port $PORT`. The first startup downloads the BGE-M3 model; allow enough RAM and disk for the model and its runtime.
