// Backend address. To change it, create frontend/.env with: VITE_API_URL=http://localhost:8000
export const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const PATHS = {
  food: "/api/food-recognition/analyze",
  freshness: "/api/freshness-detector/analyze",
  hygiene: "/api/hygiene-monitor/analyze",
  kitchen: "/api/kitchen-assistant/recipe",
  meal: "/api/meal-planner/generate",
};

export async function ping() {
  const r = await fetch(BASE + "/");
  if (!r.ok) throw new Error("offline");
  return r.json();
}

export async function post(path, body, asJson = false) {
  let res;
  try {
    res = await fetch(BASE + path, {
      method: "POST",
      headers: asJson ? { "Content-Type": "application/json" } : undefined,
      body: asJson ? JSON.stringify(body) : body,
    });
  } catch {
    throw new Error("Cannot reach the backend. Make sure run_backend.bat is running.");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    throw new Error(typeof d === "string" ? d : d ? "Please check the form: some values are missing or invalid." : `Request failed (${res.status})`);
  }
  return data;
}
