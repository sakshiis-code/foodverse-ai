import { useState } from "react";
import { ChefHat, Type, Upload, ArrowRight, ListOrdered, FileText } from "lucide-react";
import { PATHS } from "../api.js";
import { UploadBox, useAnalyze, ErrorBox } from "../components/ui.jsx";

export default function KitchenAssistant() {
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [s, run] = useAnalyze(PATHS.kitchen);
  const d = s.data;

  const submit = () => {
    const f = new FormData();
    if (text.trim()) f.append("ingredients_text", text.trim());
    if (file) f.append("file", file);
    run(f);
  };

  return (
    <div className="page narrow">
      <div className="center">
        <div className="circle big orange"><ChefHat size={30} /></div>
        <h1 className="title">Smart Recipe Generator</h1>
        <p className="sub">Describe your ingredients or upload a photo to get a full recipe.</p>
      </div>
      <div className="card">
        <div className="two">
          <label className="textbox tall"><small className="label orange"><Type size={13} /> DESCRIBE DISH / INGREDIENTS</small>
            <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="e.g. I have chicken, rice, and tomatoes. What can I make?" />
          </label>
          <div><small className="label orange"><Upload size={13} /> UPLOAD IMAGE</small>
            <UploadBox file={file} onFile={setFile} title="Click to Upload Photo" hint="" />
          </div>
        </div>
        <div className="center">
          <button className="btn orange pill-btn" disabled={(!text.trim() && !file) || s.loading} onClick={submit}>
            {s.loading ? "Cooking up a recipe..." : <>Generate Recipe <ArrowRight size={16} /></>}
          </button>
        </div>
      </div>
      {s.error && <ErrorBox message={s.error} />}
      {d && (
        <div className="card recipe">
          <div className="recipe-head"><h2>{d.recipe_name}</h2><ChefHat size={22} className="muted" /></div>
          <div className="stats-line">
            <span>Prep {d.prep_time_minutes} min</span><span>Cook {d.cook_time_minutes} min</span>
            <span>{d.servings} servings</span><span>{d.estimated_calories_per_serving} kcal / serving</span>
          </div>
          <div className="recipe-cols">
            <div>
              <h3 className="h3 orange"><FileText size={15} /> Ingredients</h3>
              <ul className="bullets">{d.ingredients.map((x, i) => <li key={i}>{x}</li>)}</ul>
              {d.missing_ingredients.length > 0 && (<><h3 className="h3 muted">You may still need</h3><ul className="bullets">{d.missing_ingredients.map((x, i) => <li key={i}>{x}</li>)}</ul></>)}
            </div>
            <div>
              <h3 className="h3 orange"><ListOrdered size={15} /> Preparation Steps</h3>
              {d.steps.map((st) => (
                <div className="step" key={st.step}><span className="num">{st.step}</span>
                  <p>{st.instruction}{st.time_minutes > 0 && <small className="muted"> ({st.time_minutes} min)</small>}</p></div>
              ))}
              {d.tips.length > 0 && (<><h3 className="h3 muted">Tips</h3><ul className="bullets">{d.tips.map((x, i) => <li key={i}>{x}</li>)}</ul></>)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
