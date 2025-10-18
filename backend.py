# backend.py — Advanced FastAPI server for AI image generation

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio, httpx, os, uuid, base64, io
from PIL import Image
from pathlib import Path

# ===================== CONFIG =====================
# Read API key from env.txt (for mobile)
env_path = Path("env.txt")
if not env_path.exists():
    raise RuntimeError("Create env.txt with your Gemini API key!")

with open(env_path, "r") as f:
    OPENAI_API_KEY = f.read().strip()

if not OPENAI_API_KEY:
    raise RuntimeError("Your Gemini API key cannot be empty in env.txt!")

SAVE_DIR = Path("generated")
SAVE_DIR.mkdir(exist_ok=True)

app = FastAPI(title="AuroraAI — Image Generator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== STORAGE =====================
JOB_RESULTS = {}

# ===================== HELPERS =====================
async def save_image_from_base64(b64_data: str) -> str:
    data = base64.b64decode(b64_data)
    image = Image.open(io.BytesIO(data))
    filename = f"{uuid.uuid4().hex}.png"
    image.save(SAVE_DIR / filename)
    return f"/generated/{filename}"

async def call_openai_image(prompt: str, size: str = "1024x1024", n: int = 1):
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    json_data = {"model": "gpt-image-1", "prompt": prompt, "n": n, "size": size}

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/images/generations",
            json=json_data,
            headers=headers
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

# ===================== ROUTES =====================
@app.post("/api/generate")
async def generate(request: Request, background: BackgroundTasks):
    payload = await request.json()
    prompt = payload.get("prompt", "").strip()
    size = payload.get("size", "1024x1024")
    n = min(max(int(payload.get("copies", 1)), 1), 5)

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    job_id = uuid.uuid4().hex

    async def process_job():
        try:
            result = await call_openai_image(prompt, size, n)
            images = []
            for img in result.get("data", []):
                if "b64_json" in img:
                    path = await save_image_from_base64(img["b64_json"])
                    images.append(path)
                elif "url" in img:
                    images.append(img["url"])
            JOB_RESULTS[job_id] = images
        except Exception as e:
            JOB_RESULTS[job_id] = {"error": str(e)}

    JOB_RESULTS[job_id] = ["processing"]
    background.add_task(process_job)
    return {"job_id": job_id, "status": "started"}

@app.get("/api/result/{job_id}")
async def result(job_id: str):
    if job_id not in JOB_RESULTS:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"images": JOB_RESULTS[job_id]}

# ===================== RUN =====================
# Run locally with:
# uvicorn backend:app --host 0.0.0.0 --port 8000