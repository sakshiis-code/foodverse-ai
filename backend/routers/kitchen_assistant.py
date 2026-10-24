"""Milestone 4.2 - Smart kitchen: recipe generation and cooking guidance."""
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from utils import ask_llm, cleanup, num, save_upload, transcribe_audio

router = APIRouter(prefix="/api/kitchen-assistant", tags=["Smart Kitchen"])


class RecipeStep(BaseModel):
    step: int
    instruction: str
    time_minutes: int = 0


class RecipeResponse(BaseModel):
    recipe_name: str
    ingredients: List[str]
    missing_ingredients: List[str]
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int
    steps: List[RecipeStep]
    tips: List[str]
    estimated_calories_per_serving: int


class AskResponse(BaseModel):
    answer: str
    tips: List[str]


@router.post("/recipe", response_model=RecipeResponse)
async def generate_recipe(
    file: Optional[UploadFile] = File(None),
    ingredients_text: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    diet: Optional[str] = Form(None),
    cuisine: Optional[str] = Form(None),
    servings: int = Form(2),
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
        typed = f"{ingredients_text or ''} {spoken}".strip()
        if not images and not typed:
            raise HTTPException(400, "Provide an ingredients photo, text or a voice note")

        prompt = f"""You are a professional chef and cooking coach.
Ingredients typed/spoken: "{typed or 'none'}"
{"Also identify the edible ingredients (or the dish) visible in the attached image." if images else ""}
Diet: {diet or 'none'} | Cuisine: {cuisine or 'any'} | Servings: {servings}
Create ONE practical recipe. Basic pantry items (salt, oil, water) are allowed.
If the image has no food or ingredients, return {{"error": "NO_INGREDIENTS"}}.
Return JSON exactly like:
{{"recipe_name": "", "ingredients": ["full list with quantities, e.g. 2 cups basmati rice"], "missing_ingredients": [""], "prep_time_minutes": 0,
  "cook_time_minutes": 0, "servings": {servings},
  "steps": [{{"instruction": "", "time_minutes": 0}}], "tips": [""], "estimated_calories_per_serving": 0}}"""
        d = ask_llm(prompt, image_paths=images or None)
        if d.get("error") == "NO_INGREDIENTS":
            raise HTTPException(400, "No ingredients could be identified")
        steps = [RecipeStep(step=i + 1, instruction=str(s.get("instruction", "")), time_minutes=int(num(s.get("time_minutes"))))
                 for i, s in enumerate(d.get("steps", [])) if isinstance(s, dict)]
        return RecipeResponse(
            recipe_name=str(d.get("recipe_name") or "Recipe"),
            ingredients=[str(x) for x in d.get("ingredients", [])],
            missing_ingredients=[str(x) for x in d.get("missing_ingredients", [])],
            prep_time_minutes=int(num(d.get("prep_time_minutes"))), cook_time_minutes=int(num(d.get("cook_time_minutes"))),
            servings=int(num(d.get("servings"), servings)), steps=steps, tips=[str(t) for t in d.get("tips", [])],
            estimated_calories_per_serving=int(num(d.get("estimated_calories_per_serving"))))
    finally:
        cleanup(temp)


@router.post("/ask", response_model=AskResponse)
async def ask_cooking_question(question: str = Form(...), recipe_context: Optional[str] = Form(None)):
    """Follow-up while cooking, e.g. 'I have no cream, what can I use instead?'"""
    d = ask_llm(f"""You are a cooking coach. Recipe context: "{recipe_context or 'none'}"
Question: "{question}"
Return JSON: {{"answer": "short clear answer", "tips": ["..."]}}""")
    return AskResponse(answer=str(d.get("answer", "")), tips=[str(t) for t in d.get("tips", [])])
