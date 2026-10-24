"""
FoodVerse AI - edge case tests (Activity 6.2).  Run run_tests.bat (backend must be running).
Prints PASS/FAIL per case and saves test_results.md for your report.
"""
import io, json, os, sys, time
import requests
from PIL import Image

BASE = "http://localhost:8000"
EP = {"food": "/api/food-recognition/analyze", "freshness": "/api/freshness-detector/analyze",
      "hygiene": "/api/hygiene-monitor/analyze", "kitchen": "/api/kitchen-assistant/recipe",
      "meal": "/api/meal-planner/generate"}
T = 180  # AI calls can be slow


def img(color=(30, 90, 200), size=(400, 400)):
    buf = io.BytesIO(); Image.new("RGB", size, color).save(buf, "JPEG"); return buf.getvalue()

def post(key, data=None, files=None, js=None):
    return requests.post(BASE + EP[key], data=data, files=files, json=js, timeout=T)

def post_slow(key, js, tries=3):
    """Meal plans are big AI requests; free Groq plans limit tokens per minute, so wait and retry if busy."""
    for i in range(tries):
        r = post(key, js=js)
        if r.status_code not in (429, 502) or i == tries - 1:
            return r
        time.sleep(45)

def body(r):
    try: return r.json()
    except Exception: return r.text[:200]

PROFILE = {"age": 25, "gender": "female", "height_cm": 165, "weight_kg": 60, "activity_level": "moderate",
           "goal": "maintain", "diet": "none", "allergies": [], "cuisine": "Indian", "days": 1, "meals_per_day": 3}

def t_root():
    r = requests.get(BASE + "/", timeout=10); return r.status_code == 200, f"HTTP {r.status_code}"
def t_food_empty():
    r = post("food"); return r.status_code == 400, f"HTTP {r.status_code} (expected 400)"
def t_food_text():
    r = post("food", data={"text_context": "2 boiled eggs and 1 slice of toast"})
    return r.status_code == 200 and body(r).get("calories", 0) > 0, f"HTTP {r.status_code}"
def t_food_notfood():
    r = post("food", files={"file": ("x.jpg", img(), "image/jpeg")}); return r.status_code < 500, f"HTTP {r.status_code}: {str(body(r))[:80]}"
def t_food_tiny():
    r = post("food", files={"file": ("t.jpg", img(size=(16, 16)), "image/jpeg")}); return r.status_code == 400, f"HTTP {r.status_code} (expected 400)"
def t_food_wrongtype():
    r = post("food", files={"file": ("a.txt", b"not an image", "text/plain")}); return r.status_code == 400, f"HTTP {r.status_code} (expected 400)"
def t_food_huge():
    r = post("food", files={"file": ("b.jpg", os.urandom(11 * 1024 * 1024), "image/jpeg")}); return r.status_code == 413, f"HTTP {r.status_code} (expected 413)"
def t_fresh_nofile():
    r = post("freshness", data={"storage_time": "2 days"}); return r.status_code == 422, f"HTTP {r.status_code} (expected 422)"
def t_fresh_blank():
    r = post("freshness", files={"file": ("w.jpg", img((255, 255, 255)), "image/jpeg")}); return r.status_code < 500, f"HTTP {r.status_code}"
def t_hyg_nofile():
    r = post("hygiene"); return r.status_code == 422, f"HTTP {r.status_code} (expected 422)"
def t_hyg_notkitchen():
    r = post("hygiene", files={"file": ("k.jpg", img((10, 10, 10)), "image/jpeg")}); return r.status_code < 500, f"HTTP {r.status_code}"
def t_kit_empty():
    r = post("kitchen"); return r.status_code == 400, f"HTTP {r.status_code} (expected 400)"
def t_kit_text():
    r = post("kitchen", data={"ingredients_text": "eggs, tomatoes, onions"}); b = body(r)
    return r.status_code == 200 and len(b.get("steps", [])) > 0, f"HTTP {r.status_code}"
def t_meal_missing():
    r = post("meal", js={"age": 25}); return r.status_code == 422, f"HTTP {r.status_code} (expected 422)"
def t_meal_badage():
    r = post("meal", js={**PROFILE, "age": -5}); return r.status_code == 422, f"HTTP {r.status_code} (expected 422)"
def t_meal_allergy():
    time.sleep(20)
    r = post_slow("meal", {**PROFILE, "allergies": ["peanuts"]})
    if r.status_code != 200: return False, f"HTTP {r.status_code}"
    b = body(r)
    items = b["today"] + b["week"]
    text = " ".join(f"{i.get('dish', '')} {i.get('summary', '')} {' '.join(map(str, i.get('ingredients', [])))}" for i in items).lower()
    text = text.replace("peanut-free", "").replace("peanut free", "").replace("no peanut", "").replace("without peanut", "")
    return "peanut" not in text, "no peanuts in dishes or ingredients" if "peanut" not in text else "PEANUT FOUND in a dish or ingredient"
def t_meal_targets():
    r = post_slow("meal", PROFILE)
    if r.status_code != 200: return False, f"HTTP {r.status_code}"
    k = body(r)["targets"]["daily_calories"]; return 1900 <= k <= 2200, f"maintenance target = {k} kcal (expected about 2085)"

TESTS = [("API root is online", t_root), ("Food: no input", t_food_empty), ("Food: text only", t_food_text),
         ("Food: non-food image", t_food_notfood), ("Food: tiny image", t_food_tiny),
         ("Food: wrong file type", t_food_wrongtype), ("Food: 11 MB file rejected", t_food_huge),
         ("Freshness: image missing", t_fresh_nofile), ("Freshness: blank image", t_fresh_blank),
         ("Hygiene: no file", t_hyg_nofile), ("Hygiene: non-kitchen image", t_hyg_notkitchen),
         ("Kitchen: empty input", t_kit_empty), ("Kitchen: text ingredients", t_kit_text),
         ("Meal: fields missing", t_meal_missing), ("Meal: invalid age", t_meal_badage),
         ("Meal: calorie target correct", t_meal_targets), ("Meal: peanut allergy respected", t_meal_allergy)]

if __name__ == "__main__":
    rows, passed = [], 0
    for name, fn in TESTS:
        try: ok, note = fn()
        except requests.ConnectionError:
            print("Cannot reach the backend. Start run_backend.bat first."); sys.exit(1)
        except Exception as e: ok, note = False, f"error: {e}"
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {name:34} {note}")
        rows.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {note} |")
    with open("test_results.md", "w", encoding="utf-8") as f:
        f.write("| Test case | Result | Notes |\n|---|---|---|\n" + "\n".join(rows) + f"\n\n**{passed}/{len(TESTS)} passed**\n")
    print(f"\n{passed}/{len(TESTS)} passed - saved to test_results.md")
