"""Milestone 5 - Personalised meal planner (profile processing, plan generation, adaptive coaching)."""
import re
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from utils import ask_llm, num

router = APIRouter(prefix="/api/meal-planner", tags=["Meal Planner"])

ACTIVITY = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
GOAL_ADJUST = {"lose_weight": -500, "maintain": 0, "gain_muscle": 300}


class UserProfile(BaseModel):
    age: int = Field(..., ge=10, le=100)
    gender: str
    height_cm: float = Field(..., ge=100, le=250)
    weight_kg: float = Field(..., ge=25, le=300)
    activity_level: str = "moderate"
    goal: str = "maintain"
    diet: str = "none"
    cuisine: str = "any"
    allergies: List[str] = []
    medical_conditions: str = "None"
    recent_history: str = "No data"


class Targets(BaseModel):
    bmr: int
    tdee: int
    daily_calories: int
    protein_g: int
    carbs_g: int
    fats_g: int
    hydration_liters: float


class MealPlanResponse(BaseModel):
    targets: Targets
    today: list
    week: list
    coach: dict
    notes: str = ""


def compute_targets(p: UserProfile) -> Targets:
    """Mifflin-St Jeor BMR -> TDEE -> goal calories -> macros -> water. Plain Python, not the LLM."""
    if p.activity_level not in ACTIVITY:
        raise HTTPException(400, f"activity_level must be one of {list(ACTIVITY)}")
    if p.goal not in GOAL_ADJUST:
        raise HTTPException(400, f"goal must be one of {list(GOAL_ADJUST)}")
    base = 10 * p.weight_kg + 6.25 * p.height_cm - 5 * p.age
    bmr = base + 5 if p.gender.lower() == "male" else base - 161
    tdee = bmr * ACTIVITY[p.activity_level]
    kcal = max(1200, tdee + GOAL_ADJUST[p.goal])
    protein = p.weight_kg * {"lose_weight": 1.8, "maintain": 1.4, "gain_muscle": 2.0}[p.goal]
    fats = kcal * 0.25 / 9
    carbs = (kcal - protein * 4 - fats * 9) / 4
    return Targets(bmr=round(bmr), tdee=round(tdee), daily_calories=round(kcal), protein_g=round(protein),
                   carbs_g=round(carbs), fats_g=round(fats), hydration_liters=max(1.5, round(p.weight_kg * 0.033, 1)))


def has_history(p: UserProfile) -> bool:
    return p.recent_history.strip().lower() not in ("", "no data", "none", "n/a")


def build_prompt(p: UserProfile, t: Targets) -> str:
    return f"""You are a registered dietitian. Create ONE detailed day with exactly these 5 meals in order:
Breakfast, Mid Morning Snack, Lunch, Evening Snack, Dinner. Their calories must add up to about {t.daily_calories} kcal
(protein about {t.protein_g} g, carbs {t.carbs_g} g, fats {t.fats_g} g in total).
Profile: age {p.age}, {p.gender}, {p.height_cm} cm, {p.weight_kg} kg. Goal: {p.goal}. Diet: {p.diet}. Cuisine: {p.cuisine}.
Medical conditions: {p.medical_conditions}. Allergies (NEVER include, not even as an ingredient): {p.allergies or 'none'}.
Recent eating history: "{p.recent_history}"
Then give a one-line summary of the meals for each day Mon-Sun (different foods each day, same rules).
Coach rules: if the history is "No data", set adherence_score to null, consistency to "Not enough data yet" and
do NOT praise past progress; give general tips for the goal instead.
Return JSON exactly like:
{{"today": [{{"meal": "Breakfast", "dish": "", "description": "", "calories": 0, "protein": 0, "carbs": 0, "fats": 0,
  "ingredients": [""], "reasoning": "why this fits the user"}}],
 "week": [{{"day": "Mon", "summary": ""}}],
 "coach": {{"adherence_score": null, "consistency": "", "suggestions": [""], "motivation": ""}},
 "notes": ""}}"""


# Foods that count as the allergen (key = allergy the user types)
RELATED = {
    "dairy": ["milk", "cheese", "yogurt", "yoghurt", "butter", "cream", "paneer", "ghee", "curd", "whey"],
    "milk": ["milk", "cheese", "yogurt", "yoghurt", "cream", "paneer", "ghee", "curd", "whey"],
    "nut": ["peanut", "almond", "cashew", "walnut", "pistachio", "hazelnut", "pecan"],
    "tree nut": ["almond", "cashew", "walnut", "pistachio", "hazelnut", "pecan"],
    "gluten": ["wheat", "bread", "pasta", "barley", "rye", "semolina", "roti", "naan", "couscous"],
    "egg": ["egg", "mayonnaise"],
    "shellfish": ["shrimp", "prawn", "crab", "lobster"],
    "soy": ["soy", "tofu", "edamame", "tempeh", "miso"],
    "fish": ["fish", "salmon", "tuna", "cod"],
    "sesame": ["sesame", "tahini"],
}


def _stem(a: str) -> str:
    a = a.lower().strip()
    return a[:-1] if len(a) > 3 and a.endswith("s") else a  # peanuts -> peanut


def find_allergens(items: list, allergies: List[str]) -> List[str]:
    """Look at dish names, descriptions and ingredients (not the AI's explanations).
    Phrases like 'peanut-free' or 'without peanuts' are ignored."""
    text = " ".join(
        " ".join(str(x) for x in [i.get("dish", ""), i.get("description", ""), i.get("summary", ""),
                                  " ".join(map(str, i.get("ingredients", []) or []))])
        for i in items if isinstance(i, dict)).lower()
    hits = []
    for a in allergies:
        stem = _stem(a)
        if not stem:
            continue
        terms = {stem}
        for key, foods in RELATED.items():
            if stem == key or stem.endswith(" " + key):
                terms.update(foods)
        for t in terms:
            cleaned = re.sub(rf"(no|without|free of|free from)\s+{re.escape(t)}\w*|{re.escape(t)}\w*[- ]free", " ", text)
            if t in cleaned:
                hits.append(a)
                break
    return hits


def _generate(profile: UserProfile, targets: Targets, warning: str = ""):
    d = ask_llm(build_prompt(profile, targets) + warning, max_tokens=8000)
    today = d.get("today") if isinstance(d.get("today"), list) else []
    week = d.get("week") if isinstance(d.get("week"), list) else []
    if not today:
        raise HTTPException(502, "Could not generate a meal plan, please try again")
    return d, today, week


@router.post("/generate", response_model=MealPlanResponse)
async def generate_plan(profile: UserProfile):
    targets = compute_targets(profile)
    d, today, week = _generate(profile, targets)

    hits = find_allergens(today + week, profile.allergies)
    if hits:  # safety net: try once more, telling the AI exactly what to remove
        d, today, week = _generate(profile, targets, f"\nIMPORTANT: your previous plan contained forbidden items related to {hits}. "
                                   "Remove them completely, including from ingredients and sauces.")
        hits = find_allergens(today + week, profile.allergies)
        if hits:
            raise HTTPException(502, f"Could not build a plan free of {hits}. Please try again.")

    c = d.get("coach") if isinstance(d.get("coach"), dict) else {}
    history = has_history(profile)
    adherence = None
    if history and c.get("adherence_score") is not None:
        adherence = max(0, min(100, int(num(c.get("adherence_score")))))
    coach = {"adherence_score": adherence,
             "consistency": str(c.get("consistency", "")) if history else "Not enough data yet",
             "suggestions": [str(x) for x in c.get("suggestions", [])],
             "motivation": str(c.get("motivation", ""))}
    return MealPlanResponse(targets=targets, today=today, week=week, coach=coach, notes=str(d.get("notes", "")))
