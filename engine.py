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
    images = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(min(len(doc), max_pages)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=120)
            img = Image.open(io.BytesIO(pix.tobytes("jpeg")))
            images.append(img)
    except Exception as e:
        print(f"PDF Error: {e}")
    return images

def chat(prompt: str, file_bytes: bytes = None, mime_type: str = None, history: list = None) -> str:
    client = get_client()
    
    system_instruction = (
        "You are SnapStudy, an expert Nigerian university study buddy. "
        "Provide concise, direct answers with bold key terms and bullet points. "
        "Keep it very fast and readable for mobile students."
    )
    
    contents = []
    if file_bytes:
        if mime_type and mime_type.startswith("image/"):
            img = Image.open(io.BytesIO(file_bytes))
            contents.append(img)
        elif mime_type == "application/pdf":
            pdf_images = convert_pdf_to_images(file_bytes)
            contents.extend(pdf_images)
            
    if prompt:
        contents.append(prompt)
    elif not contents:
        contents.append("Hello! How can I help you study today?")

    # CORRECTED MODEL NAMES
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-flash-8b"]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.4,
                )
            )
            return response.text
        except Exception as e:
            print(f"Failed with {model_name}: {e}")
            continue

    return "AI is temporarily busy. Please send your message again in a few seconds!"
