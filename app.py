"""
SnapStudy Web Server — Run this to start the website!
"""

import os
import uuid
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from engine import snap_study

app = FastAPI()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
   return templates.TemplateResponse(request, "index.html")


@app.post("/api/snap")
async def snap(image: UploadFile = File(...)):
    # Save uploaded file temporarily
    file_id = str(uuid.uuid4())[:8]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.jpg")

    with open(file_path, "wb") as f:
        content = await image.read()
        f.write(content)

    # Process with AI
    result = snap_study(file_path)

    # Clean up
    try:
        os.remove(file_path)
    except:
        pass

    return result


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("⚡ SnapStudy is running!")
    print("📱 Open this on your phone:")
    print("   http://127.0.0.1:8000")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)