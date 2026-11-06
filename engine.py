import os
import fitz
from PIL import Image
import io
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_client():
    return genai.Client(api_key=GEMINI_API_KEY)

def convert_pdf_to_images(pdf_bytes, max_pages=5):
    images = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(min(len(doc), max_pages)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=120)
            img = Image.open(io.BytesIO(pix.tobytes("jpeg")))
            images.append(img)
    except:
        pass
    return images

def chat(prompt: str, file_bytes: bytes = None, mime_type: str = None, history: list = None) -> str:
    client = get_client()
    
    system_instruction = (
        "You are SnapStudy, the ultimate Nigerian university AI tutor. "
        "Provide fast, accurate, and structured answers with bold key terms. "
        "Keep responses optimized for mobile reading."
    )
    
    contents = []
    if file_bytes:
        if mime_type and mime_type.startswith("image/"):
            img = Image.open(io.BytesIO(file_bytes))
            contents.append(img)
        elif mime_type == "application/pdf":
            contents.extend(convert_pdf_to_images(file_bytes))
            
    if prompt:
        contents.append(prompt)

    # THE WATERFALL: Tried in order of "Best" to "Fastest"
    models_to_try = [
        "gemini-2.0-flash",            # Elite & Newest
        "gemini-2.0-flash-lite-preview-02-05", # Fastest 2.0 version
        "gemini-1.5-flash",            # Extremely reliable
        "gemini-1.5-flash-8b",         # Small & Lightning fast
        "gemini-1.5-pro"               # Deep thinker (slower backup)
    ]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                )
            )
            return response.text
        except Exception as e:
            # If one model is busy, it silently jumps to the next one in the list
            print(f"Skipping {model_name} due to congestion...")
            continue

    return "All AI lanes are currently full in your region. Please try again in 10 seconds!"
