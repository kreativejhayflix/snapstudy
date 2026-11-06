import os
import fitz  # PyMuPDF
from PIL import Image
import io
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    return genai.Client(api_key=GEMINI_API_KEY)

def convert_pdf_to_images(pdf_bytes, max_pages=5):
    """Converts up to max_pages of a PDF into compressed images for fast processing."""
    images = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page_num in range(min(len(doc), max_pages)):
        page = doc.load_page(page_num)
        # 120 DPI provides sharp handwriting reading while keeping file size small & fast
        pix = page.get_pixmap(dpi=120)
        img = Image.open(io.BytesIO(pix.tobytes("jpeg")))
        images.append(img)
    return images

def chat(prompt: str, file_bytes: bytes = None, mime_type: str = None, history: list = None) -> str:
    client = get_client()
    
    # System prompt optimized for speed & clear, concise Nigerian mobile study responses
    system_instruction = (
        "You are SnapStudy, an expert Nigerian university study buddy. "
        "Keep answers concise, direct, clear, and quick to read on mobile screens. "
        "Use simple formatting, bold key terms, and bullet points. Avoid unnecessary fluff."
    )
    
    contents = []
    
    # Process file if provided
    if file_bytes:
        if mime_type and mime_type.startswith("image/"):
            img = Image.open(io.BytesIO(file_bytes))
            contents.append(img)
        elif mime_type == "application/pdf":
            pdf_images = convert_pdf_to_images(file_bytes)
            contents.extend(pdf_images)
            
    # Include student message
    if prompt:
        contents.append(prompt)
    elif not contents:
        contents.append("Hello! How can I help with your studies today?")

    # Recommended fast Gemini models loop
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.4, # Lower temperature = faster, focused output
                )
            )
            return response.text
        except Exception as e:
            continue

    return "Sorry, I am having trouble connecting right now. Please try again!"
