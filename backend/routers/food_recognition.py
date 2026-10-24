"""Milestone 2 - Food recognition, nutrition estimation and health scoring."""
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from utils import ask_llm, cleanup, num, save_upload, transcribe_audio

router = APIRouter(prefix="/api/food-recognition", tags=["Food Recognition"])


class FoodResponse(BaseModel):
    dish_name: str
    calories: int
    protein: float
    carbs: float
    fats: float
    fiber: float
    sugar: float
    health_score: int
    health_label: str
    reasoning: str
    alternatives: List[str]


@router.post("/analyze", response_model=FoodResponse)
async def analyze(
    file: Optional[UploadFile] = File(None),
    text_context: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
):
    temp = []
    try:
        images = []
        if file:
            p = save_upload(file)
            temp.append(p)
            images.append(p)
        spoken = ""
        if audio_file:
            ap = save_upload(audio_file, kinds=("audio/", "video/webm"))
            temp.append(ap)
            spoken = transcribe_audio(ap)
        context = f"{text_context or ''} {spoken}".strip()
        if not images and not context:
            raise HTTPException(400, "No input provided: add a photo, text or a voice note")

        prompt = f"""You are a professional AI nutritionist and food technologist.
{"Analyze the attached image to identify the food." if images else "Identify the food from the description only."}
User context (use it to refine portion size / ingredients): "{context or 'none'}"

RULES:
1. Check first: is this food or a drink? If NOT (person, car, animal, document...), return exactly {{"error": "NOT_FOOD"}}
2. Otherwise estimate nutrition for the visible portion.

Return JSON exactly like:
{{"dish_name": "", "calories": 0, "protein": 0, "carbs": 0, "fats": 0, "fiber": 0, "sugar": 0,
  "health_score": 0, "reasoning": "short explanation", "alternatives": ["healthier option 1", "option 2"]}}
(protein/carbs/fats/fiber/sugar are grams; health_score is 0-100 based on nutrient balance and calorie density)"""
        d = ask_llm(prompt, image_paths=images or None)
        if d.get("error") == "NOT_FOOD":
            raise HTTPException(400, "This does not look like food or a drink")

        score = max(0, min(100, int(num(d.get("health_score")))))
        label = "Healthy" if score >= 70 else "Moderate" if score >= 40 else "Unhealthy"
        return FoodResponse(
            dish_name=str(d.get("dish_name") or "Unknown dish"),
            calories=int(num(d.get("calories"))), protein=num(d.get("protein")), carbs=num(d.get("carbs")),
            fats=num(d.get("fats")), fiber=num(d.get("fiber")), sugar=num(d.get("sugar")),
            health_score=score, health_label=label,
            reasoning=str(d.get("reasoning", "")), alternatives=[str(a) for a in d.get("alternatives", [])])
    finally:
        cleanup(temp)
