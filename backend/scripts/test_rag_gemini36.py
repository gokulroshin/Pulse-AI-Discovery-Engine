import os
from google import genai
from google.genai import types
from app.config import settings

api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
client = genai.Client(api_key=api_key)

prompt = """USER QUESTION: Do users face decision fatigue while choosing?
RETRIEVED MULTI-CHANNEL EVIDENCE:
[1] Platform: REDDIT | Quote: "I spent 2 hours scrolling through 50 kurtas that all look the same with slight color difference, ended up closing the app with headache." | Cause: Catalog overwhelming similarity and analysis paralysis
[2] Platform: APPSTORE | Quote: "Too many options with confusing size charts. Every brand has a different size chart so I can't decide." | Cause: Size chart inconsistency across brands causing hesitation
[3] Platform: REDDIT | Quote: "Wishlisted 15 dresses for a farewell party, but comparing reviews on fabric transparency across all of them made me give up." | Cause: Review comparison fatigue

Synthesize a structured JSON response with summary, detailed_synthesis, key_drivers, and segment_nuances."""

res = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt,
    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2),
)
print("RESULT:\n", res.text)
