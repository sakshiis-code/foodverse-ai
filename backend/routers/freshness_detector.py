"""Milestone 3 - Freshness and spoilage detection with safety recommendations."""
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from utils import ask_llm, cleanup, num, save_upload, transcribe_audio

router = APIRouter(prefix="/api/freshness-detector", tags=["Freshness Detector"])

SAFETY = {"Fresh": "Safe to Eat", "Moderate": "Consume Soon", "Spoiled": "Unsafe", "Unknown": "Unknown"}


class FreshnessResponse(BaseModel):
    item_name: str
    freshness_level: str
    confidence: int
    safety_status: str
    detected_signs: List[str]
    reasoning: str
    recommendation: str


@router.post("/analyze", response_model=FreshnessResponse)
async def analyze_freshness(
    file: UploadFile = File(...),
    storage_time: Optional[str] = Form(None),
    storage_type: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
):
    temp = []
    try:
        path = save_upload(file)
        temp.append(path)
        note = ""
        if audio_file:
            ap = save_upload(audio_file, kinds=("audio/", "video/webm"))
            temp.append(ap)
            note = transcribe_audio(ap)

        prompt = f"""You are an AI food quality inspector.
Judge freshness from what is VISIBLE in the image. Storage info and the user's smell/texture note are only
supporting context and must never override clear visual evidence.
Storage: {storage_time or 'unknown'} in {storage_type or 'unknown'}. User note (smell/texture): "{note or 'none'}"

If the image is not food, return exactly {{"error": "NOT_FOOD"}}.

Levels:
- "Fresh": vibrant colour, firm, no spots or mould.
- "Moderate": minor browning, soft spots, slight wilting - still edible soon.
- "Spoiled": mould, heavy dark/black discolouration, slime, shrivelling, mushy.
(Bananas: yellow = Fresh, brown spots = Moderate, black/dark brown = Spoiled.)

Return JSON exactly like:
{{"item_name": "", "freshness_level": "Fresh|Moderate|Spoiled", "confidence": 90,
  "detected_signs": ["sign 1"], "reasoning": "based on visual evidence", "recommendation": "advice"}}"""
        d = ask_llm(prompt, image_paths=[path])
        if d.get("error") == "NOT_FOOD":
            raise HTTPException(400, "This does not look like food")

        raw = str(d.get("freshness_level", "")).lower()
        level = "Spoiled" if "spoil" in raw else "Moderate" if "moder" in raw else "Fresh" if "fresh" in raw else "Unknown"
        return FreshnessResponse(
            item_name=str(d.get("item_name") or "Unknown"), freshness_level=level,
            confidence=max(0, min(100, int(num(d.get("confidence"))))),
            safety_status=SAFETY[level],  # derived in code so it always matches the level
            detected_signs=[str(s) for s in d.get("detected_signs", [])],
            reasoning=str(d.get("reasoning", "")), recommendation=str(d.get("recommendation", "")))
    finally:
        cleanup(temp)
