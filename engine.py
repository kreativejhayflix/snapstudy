"""
SnapStudy Engine v4 — Chat-based AI study assistant.
Supports text chat, photos, and PDFs with conversation memory.
"""

import os
import json
import time
from google import genai
from dotenv import load_dotenv
from PIL import Image
import fitz

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.0-flash"]

SYSTEM_PROMPT = """You are SnapStudy, a friendly AI study buddy for Nigerian university students.

Your personality:
- Warm, encouraging, and patient — like a smart friend who helps with studying
- Use simple, clear language — avoid overly academic jargon
- Be concise — students are in a hurry, especially during exam season
- Use emojis occasionally to keep things fun 📚⚡
- If a student seems confused, break things down step by step
- Offer to quiz them after explaining a topic
- You understand the Nigerian university context (semesters, carry-overs, CGPA, past questions, etc.)

What you can do:
- Explain any topic from any course (Engineering, Medicine, Law, Sciences, Arts, Business, etc.)
- Analyze photos of lecture notes, textbooks, whiteboards, or past questions
- Read and summarize PDF handouts and slides
- Create practice quizzes on any topic
- Help with assignments (guide them, don't just give answers)
- Predict likely exam questions based on topics
- Simplify complex formulas and theories

Rules:
- If a student uploads an image or PDF, analyze it thoroughly and explain the content
- If they ask a follow-up question about the image/PDF, use your previous analysis
- Keep responses under 300 words unless the student asks for more detail
- If you don't know something, be honest — don't make things up
- Format your responses clearly with bullet points and bold text when helpful
- Never refuse to help with a study-related question"""


def pdf_to_images(pdf_path, max_pages=3):
    """Convert PDF pages to PIL Images."""
    images = []
    try:
        doc = fitz.open(pdf_path)
        total_pages = min(len(doc), max_pages)
        for page_num in range(total_pages):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        doc.close()
    except Exception as e:
        print(f"Error converting PDF: {e}")
    return images


def chat(message, history=None, file_path=None):
    """
    Chat with the AI. Supports text, images, and PDFs.
    history: list of {"role": "user"/"assistant", "content": "..."}
    """
    if history is None:
        history = []

    # Build the conversation for Gemini
    contents = []

    # Add system prompt as the first user message
    contents.append({"role": "user", "parts": [{"text": SYSTEM_PROMPT}]})
    contents.append({"role": "model", "parts": [{"text": "Got it! I'm SnapStudy, your study buddy. Let's ace these exams together! ⚡📚"}]})

    # Add conversation history (last 10 messages to save tokens)
    recent_history = history[-10:] if len(history) > 10 else history
    for msg in recent_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    # Build the current message
    current_parts = []

    # Handle file attachment
    if file_path and os.path.exists(file_path):
        is_pdf = file_path.lower().endswith(".pdf")

        if is_pdf:
            images = pdf_to_images(file_path, max_pages=3)
            if images:
                for img in images:
                    current_parts.append(img)
                file_note = f"[Student uploaded a PDF with {len(images)} page(s)]. "
            else:
                file_note = "[Student tried to upload a PDF but it couldn't be read]. "
        else:
            try:
                img = Image.open(file_path)
                current_parts.append(img)
                file_note = "[Student uploaded a photo of their notes]. "
            except Exception:
                file_note = "[Student tried to upload an image but it couldn't be read]. "

        # Combine file note with message
        if message.strip():
            current_parts.append({"text": file_note + message})
        else:
            current_parts.append({"text": file_note + "Please analyze this and explain the key concepts."})
    else:
        current_parts.append({"text": message})

    contents.append({"role": "user", "parts": current_parts})

    # Try each model with retries
    for model_name in MODELS:
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
                return response.text

            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg or "UNAVAILABLE" in error_msg:
                    time.sleep(10)
                    continue
                elif "404" in error_msg or "NOT_FOUND" in error_msg:
                    break
                elif "429" in error_msg:
                    time.sleep(30)
                    continue
                else:
                    return f"Sorry, something went wrong 😅 Error: {e}"

    return "Sorry, the AI servers are really busy right now 😓 Try again in a minute!"
