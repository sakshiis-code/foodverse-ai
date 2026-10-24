from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import food_recognition, freshness_detector, hygiene_monitor, kitchen_assistant, meal_planner

app = FastAPI(title="FoodVerse AI", description="Multimodal AI Platform for Food Analysis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to FoodVerse AI API", "status": "active",
            "api_key_set": bool(os.environ.get("GROQ_API_KEY"))}


@app.get("/models")
def list_models():
    """Troubleshooting: which Groq models can your API key use right now?"""
    from utils import client, candidates, TEXT_MODELS, VISION_MODELS
    try:
        available = sorted(m.id for m in client.models.list().data)
    except Exception as e:
        return {"error": str(e)}
    return {"will_try_for_text": candidates(TEXT_MODELS, False), "will_try_for_images": candidates(VISION_MODELS, True),
            "all_models_your_key_can_use": available}


@app.get("/diagnose")
def diagnose():
    """Troubleshooting: tries one tiny text request and one tiny image request and shows the exact result."""
    from PIL import Image
    from utils import ask_llm, UPLOAD_DIR
    out = {}
    try:
        out["text_model"] = ask_llm('Return JSON: {"ok": true}')
    except Exception as e:
        out["text_model"] = "FAILED: " + str(getattr(e, "detail", e))
    path = os.path.join(UPLOAD_DIR, "diagnose.jpg")
    Image.new("RGB", (64, 64), (200, 30, 30)).save(path, "JPEG")
    try:
        out["vision_model"] = ask_llm('The image is one solid colour. Return JSON: {"colour": "name"}', image_paths=[path])
    except Exception as e:
        out["vision_model"] = "FAILED: " + str(getattr(e, "detail", e))
    finally:
        try: os.remove(path)
        except OSError: pass
    return out


for r in (food_recognition, freshness_detector, hygiene_monitor, kitchen_assistant, meal_planner):
    app.include_router(r.router)
