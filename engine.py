"""
SnapStudy Engine v2 — Returns structured JSON for the web app.
"""

import os
import json
import time
from google import genai
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.0-flash"]

JSON_PROMPT = """You are SnapStudy, an AI study assistant for Nigerian university students.

Analyze the uploaded image of lecture notes, textbook, or past questions.

You MUST respond with ONLY a valid JSON object (no markdown, no explanation outside JSON).

Use this exact structure:
{
  "topic": "The main topic in 3-5 words",
  "study_guide": "A clear, simplified summary of everything in the image. Use simple language. Break complex ideas into short paragraphs.",
  "key_concepts": [
    {"term": "Term name", "definition": "Simple one-line definition"},
    {"term": "Term name", "definition": "Simple one-line definition"}
  ],
  "flashcards": [
    {"front": "Question or term", "back": "Answer or definition"},
    {"front": "Question or term", "back": "Answer or definition"}
  ],
  "questions": [
    {
      "question": "Exam-style question?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "answer": 0,
      "explanation": "Why this answer is correct"
    }
  ],
  "exam_predictions": [
    {"topic": "Likely exam topic", "reason": "Why it will likely appear"}
  ]
}

Rules:
- Include 5-8 key concepts
- Include 6-10 flashcards
- Include 4-6 quiz questions (mix of easy and hard)
- Include 2-3 exam predictions
- The 'answer' field is the INDEX of the correct option (0, 1, 2, or 3)
- Keep everything concise
- If the image contains past questions, answer and explain them
- Return ONLY valid JSON, nothing else"""


def snap_study(image_path):
    if not os.path.exists(image_path):
        return {"error": "File not found"}

    try:
        img = Image.open(image_path)
    except Exception as e:
        return {"error": f"Cannot open image: {e}"}

    for model_name in MODELS:
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[JSON_PROMPT, img]
                )

                text = response.text.strip()
                # Remove markdown code blocks if present
                if text.startswith("```"):
                    text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text.rsplit("```", 1)[0]
                text = text.strip()

                data = json.loads(text)
                return data

            except json.JSONDecodeError:
                return {
                    "topic": "Study Notes",
                    "study_guide": text if 'text' in dir() else "Could not parse response.",
                    "key_concepts": [],
                    "flashcards": [],
                    "questions": [],
                    "exam_predictions": []
                }

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
                    return {"error": str(e)}

    return {"error": "All models failed. Try again later."}