"""Milestone 4.1 - Kitchen hygiene detection and compliance scoring (image or video)."""
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from utils import ask_llm, cleanup, extract_video_frames, num, save_upload

router = APIRouter(prefix="/api/hygiene-monitor", tags=["Hygiene Monitor"])

CHECKLIST = ["gloves_worn", "hairnet_or_cap_worn", "clean_apron_or_uniform", "clean_work_surfaces",
             "raw_cooked_separation", "no_pests_or_waste_visible", "proper_food_storage",
             "handwashing_or_sanitizer_available", "no_phone_use"]


class CheckItem(BaseModel):
    item: str
    status: str  # pass | fail | not_visible
    note: str = ""


class Violation(BaseModel):
    violation: str
    severity: str  # High | Medium | Low
    location: str = ""
    reason: str = ""


class HygieneResponse(BaseModel):
    compliance_score: int
    grade: str
    floor_score: int
    summary: str
    checklist: List[CheckItem]
    violations: List[Violation]
    recommendations: List[str]
    frames_analyzed: int


def grade_for(score: int) -> str:
    return "A - Excellent" if score >= 90 else "B - Good" if score >= 75 else "C - Needs improvement" if score >= 60 else "D - Critical"


@router.post("/analyze", response_model=HygieneResponse)
async def analyze_hygiene(file: UploadFile = File(...), notes: Optional[str] = Form(None)):
    temp = []
    try:
        path = save_upload(file, kinds=("image/", "video/"), max_mb=50)
        temp.append(path)
        if (file.content_type or "").startswith("video/"):
            images = extract_video_frames(path, max_frames=3)
            temp.extend(images)
        else:
            images = [path]

        prompt = f"""You are a food-safety inspector reviewing kitchen images (frames of one video if several).
If they do NOT show a kitchen, food area or food handlers, return {{"error": "NOT_KITCHEN"}}.
Rate each checklist item "pass", "fail" or "not_visible" (use not_visible if you cannot see enough).
Checklist: {CHECKLIST}
Rules from the user: "{notes or 'Gloves mandatory. Hairnets required. No phone use.'}"
Also rate floor cleanliness 0-100 (100 = spotless) and list each violation with severity High/Medium/Low.
Return JSON exactly like:
{{"checklist": [{{"item": "gloves_worn", "status": "pass", "note": "short evidence"}}],
  "floor_score": 90,
  "violations": [{{"violation": "No Gloves", "severity": "High", "location": "Prep table", "reason": "Handling food without gloves"}}],
  "recommendations": ["..."], "summary": "2 sentence assessment"}}"""
        d = ask_llm(prompt, image_paths=images)
        if d.get("error") == "NOT_KITCHEN":
            raise HTTPException(400, "This does not look like a kitchen or food-handling area")

        items = []
        for c in d.get("checklist", []):
            st = str(c.get("status", "not_visible")).lower()
            items.append(CheckItem(item=str(c.get("item", "")), status=st if st in ("pass", "fail", "not_visible") else "not_visible",
                                   note=str(c.get("note", ""))))
        violations = []
        for v in d.get("violations", []):
            if isinstance(v, dict):
                sev = str(v.get("severity", "Medium")).capitalize()
                violations.append(Violation(violation=str(v.get("violation", "")), severity=sev if sev in ("High", "Medium", "Low") else "Medium",
                                            location=str(v.get("location", "")), reason=str(v.get("reason", ""))))
        passed, failed = sum(i.status == "pass" for i in items), sum(i.status == "fail" for i in items)
        score = round(passed / (passed + failed) * 100) if passed + failed else 0  # computed in code, not by the AI
        return HygieneResponse(
            compliance_score=score, grade=grade_for(score) if passed + failed else "Not enough visible evidence",
            floor_score=max(0, min(100, int(num(d.get("floor_score"))))),
            summary=str(d.get("summary", "")), checklist=items, violations=violations,
            recommendations=[str(r) for r in d.get("recommendations", [])], frames_analyzed=len(images))
    finally:
        cleanup(temp)
