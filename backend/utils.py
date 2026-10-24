"""Shared helpers: upload handling, audio, images/video, and the Groq LLM call."""
import base64, io, json, os, re, uuid

import cv2
import numpy as np
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile
from groq import Groq
from PIL import Image

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
# Groq retires models often. Change these in backend/.env (GROQ_TEXT_MODEL / GROQ_VISION_MODEL),
# and open http://localhost:8000/models to see which models your key can use right now.
def _models(env_name, defaults):
    chosen = os.environ.get(env_name)
    return ([chosen] if chosen else []) + [m for m in defaults if m != chosen]

import time
_cache = {"ids": [], "at": 0.0}
_SKIP = re.compile(r"(whisper|guard|safeguard|tts|orpheus|compound|embed|moderation)", re.I)
_VISION_HINT = re.compile(r"(vision|scout|maverick|qwen3\.[5-9]|qwen-?vl|pixtral|llava|gemma-?[34])", re.I)
_TEXT_HINT = re.compile(r"(gpt-oss|llama|qwen|kimi|gemma)", re.I)


def available_models():
    """Model ids your Groq key can use right now (cached for 10 minutes)."""
    if time.time() - _cache["at"] > 600:
        try:
            _cache["ids"] = [m.id for m in client.models.list().data]
        except Exception:
            _cache["ids"] = []
        _cache["at"] = time.time()
    return _cache["ids"]


def candidates(preferred, vision):
    """Preferred models that exist for this key, then any other suitable ones Groq offers."""
    avail = available_models()
    if not avail:  # could not list models: just try the preferred ones
        return list(preferred)
    out = [m for m in preferred if m in avail]
    hint = _VISION_HINT if vision else _TEXT_HINT
    out += [m for m in avail if m not in out and not _SKIP.search(m) and hint.search(m)]
    return out


TEXT_MODELS = _models("GROQ_TEXT_MODEL", ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"])
VISION_MODELS = _models("GROQ_VISION_MODEL", ["qwen/qwen3.6-27b", "qwen/qwen3.8-27b"])
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def num(v, default=0.0):
    """Turn '37g' / 37 / None into a float safely."""
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(v)))
    except ValueError:
        return default


def save_upload(upload: UploadFile, kinds=("image/",), max_mb: int = 10) -> str:
    """Validate type + size; save under a random name (no collisions, no path tricks)."""
    ctype = upload.content_type or ""
    if not ctype.startswith(tuple(kinds)):
        raise HTTPException(400, f"Unsupported file type '{ctype}'. Allowed: {', '.join(kinds)}")
    ext = re.sub(r"[^a-zA-Z0-9.]", "", os.path.splitext(upload.filename or "")[1])[:8]
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    size, too_big = 0, False
    with open(path, "wb") as out:
        while chunk := upload.file.read(1024 * 1024):
            size += len(chunk)
            if size > max_mb * 1024 * 1024:
                too_big = True
                break
            out.write(chunk)
    if too_big:
        os.remove(path)
        raise HTTPException(413, f"File too large (max {max_mb} MB)")
    return path


def cleanup(paths):
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except OSError:
            pass


def transcribe_audio(path: str) -> str:
    """Audio -> text ('' if it cannot be understood). Needs ffmpeg installed."""
    import speech_recognition as sr
    from pydub import AudioSegment
    wav = path + ".wav"
    try:
        AudioSegment.from_file(path).export(wav, format="wav")
        rec = sr.Recognizer()
        with sr.AudioFile(wav) as src:
            return rec.recognize_google(rec.record(src))
    except Exception:
        return ""
    finally:
        cleanup([wav])


def image_to_data_url(path: str, max_side: int = 1024) -> str:
    """Resize + convert to RGB JPEG (preprocessing), then base64 for the vision model."""
    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        raise HTTPException(400, "Could not read the image file")
    if min(img.size) < 64:
        raise HTTPException(400, "Image is too small to analyze. Please upload a larger photo (at least 64x64 pixels).")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def extract_video_frames(video_path: str, max_frames: int = 5):
    """Pick evenly spaced frames from a video and save them as JPEGs."""
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        raise HTTPException(400, "Could not read the video file")
    paths = []
    for idx in np.linspace(0, total - 1, min(max_frames, total)).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if ok:
            p = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.jpg")
            cv2.imwrite(p, frame)
            paths.append(p)
    cap.release()
    if not paths:
        raise HTTPException(400, "No frames could be extracted from the video")
    return paths


def parse_json(text: str) -> dict:
    """Parse JSON even if the model wrapped it in ```json fences or added extra text."""
    text = re.sub(r"```(?:json)?", "", text or "").strip()
    a, b = text.find("{"), text.rfind("}")
    if a == -1 or b == -1:
        raise ValueError("No JSON found")
    return json.loads(text[a:b + 1])


def _chat(model, messages, max_tokens):
    """One Groq call. Retries without optional settings if the model rejects them."""
    json_mode = {"response_format": {"type": "json_object"}}
    effort = "low" if model.startswith("openai/gpt-oss") else "none" if model.startswith("qwen/") else None
    options = [{**json_mode, **({"reasoning_effort": effort} if effort else {})}, json_mode, {}]
    last = None
    for extra in options:
        try:
            return client.chat.completions.create(model=model, messages=messages, temperature=0.2,
                                                  max_completion_tokens=max_tokens, **extra)
        except Exception as e:
            last = e
            msg = str(e).lower()
            if "429" in msg or "rate limit" in msg:
                raise  # not an option problem: let the caller wait and retry
            if "model" in msg and ("not exist" in msg or "decommission" in msg or "not found" in msg):
                raise
    raise last


def ask_llm(prompt: str, image_paths=None, system="You are a helpful assistant. Respond with valid JSON only.", max_tokens: int = 4000):
    """Call Groq (vision model if images given, else text model). Returns a dict."""
    if image_paths:
        content = [{"type": "text", "text": prompt}] + [
            {"type": "image_url", "image_url": {"url": image_to_data_url(p)}} for p in image_paths]
        models = candidates(VISION_MODELS, vision=True)
        max_tokens = min(max_tokens, 2500)
        if not models:
            raise HTTPException(502, "Your Groq key cannot use any image-capable model right now. Models it can use: "
                                     f"{available_models()}. Check http://localhost:8000/models and your Groq console "
                                     "(console.groq.com) for model access, or set GROQ_VISION_MODEL in backend/.env")
    else:
        content, models = prompt, candidates(TEXT_MODELS, vision=False)
        if not models:
            raise HTTPException(502, f"No text model is available for your Groq key. Models it can use: {available_models()}")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": content}]

    resp, last_err = None, None
    for model in models:
        for attempt in (1, 2):
            try:
                resp = _chat(model, messages, max_tokens)
                break
            except Exception as e:
                last_err = e
                if attempt == 1 and ("429" in str(e) or "rate limit" in str(e).lower()):
                    time.sleep(20)  # free plans limit tokens per minute: wait, then retry once
                    continue
                break
        if resp is not None:
            break
    if resp is None:
        raise HTTPException(502, f"AI service error (tried {models}): {last_err}. Open http://localhost:8000/models to see which "
                                 "models your key can use, then set GROQ_TEXT_MODEL / GROQ_VISION_MODEL in backend/.env")
    try:
        return parse_json(resp.choices[0].message.content or "")
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(502, "AI returned an invalid response, please try again")
