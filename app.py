"""
SnapStudy Web Server v3 — Chat-based API.
"""

import os
import uuid
import json
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from engine import chat

app = FastAPI()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf"}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/api/chat")
async def chat_endpoint(
    message: str = Form(""),
    history: str = Form("[]"),
    file: UploadFile = File(None)
):
    # Parse conversation history
    try:
        chat_history = json.loads(history)
    except:
        chat_history = []

    # Handle file upload
    file_path = None
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return {"response": f"Sorry, I can't read {ext} files yet 😅 Use JPG, PNG, or PDF!"}

        file_id = str(uuid.uuid4())[:8]
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

    # Get AI response
    if not message.strip() and not file_path:
        return {"response": "Type a question or upload a photo to get started! 📚"}

    ai_response = chat(message, chat_history, file_path)

    # Clean up uploaded file
    if file_path:
        try:
            os.remove(file_path)
        except:
            pass

    return {"response": ai_response}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print("=" * 50)
    print("⚡ SnapStudy Chat is running!")
    print(f"📱 Open: http://127.0.0.1:{port}")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=port)
