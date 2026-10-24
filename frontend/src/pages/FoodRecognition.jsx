import { useState } from "react";
import { Flame, Activity, Wheat, Droplets, Check, Type, Utensils, Sparkles, Zap } from "lucide-react";
import { PATHS } from "../api.js";
import { UploadBox, MicButton, useRecorder, voiceFile, useAnalyze, Placeholder, ErrorBox, Ring, Tile } from "../components/ui.jsx";

export default function FoodRecognition() {
  const [file, setFile] = useState(null);
  const [text, setText] = useState("");
  const rec = useRecorder();
  const [s, run] = useAnalyze(PATHS.food);
  const ready = file || text.trim() || rec.blob;

  const submit = () => {
    const f = new FormData();
    if (file) f.append("file", file);
    if (text.trim()) f.append("text_context", text.trim());
    if (rec.blob) f.append("audio_file", voiceFile(rec.blob));
    run(f);
  };
  const d = s.data;

  return (
    <div className="page">
      <h1 className="title green">Multimodal Food Lens <Sparkles size={22} color="#facc15" /></h1>
      <p className="sub">Combine Image + Voice + Text for the most accurate nutrition AI.</p>
      <div className="grid2">
        <div className="stack">
          <UploadBox file={file} onFile={setFile} title="Upload Food Image" hint="Drag & drop or click to browse" tall />
          <div className="card">
            <small className="label"><Activity size={13} /> ADD CONTEXT (OPTIONAL)</small>
            <div className="two">
              <MicButton rec={rec} />
              <label className="textbox"><small><Type size={12} /> DESCRIPTION / GOALS</small>
                <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="What is this?" />
              </label>
            </div>
          </div>
          <button className="btn green" disabled={!ready || s.loading} onClick={submit}>{s.loading ? "Analyzing..." : "Analyze Meal"}</button>
        </div>

        <div className="stack">
          {s.error && <ErrorBox message={s.error} />}
          {!d && !s.error && <Placeholder Icon={Utensils} title={s.loading ? "Analyzing your meal..." : "Ready to Analyze"} text="Upload a photo and optionally add voice notes to generate nutrition insights." />}
          {d && (
            <>
              <div className="card">
                <div className="dish-head">
                  <div>
                    <small className="label green">IDENTIFIED DISH</small>
                    <h2 className="dish">{d.dish_name}</h2>
                    <span className="tag"><Zap size={12} /> Llama 4 Scout analysis</span>
                  </div>
                  <Ring value={d.health_score} />
                </div>
                <div className="tiles">
                  <Tile Icon={Flame} color="#f97316" value={d.calories} unit=" kcal" label="CALORIES" />
                  <Tile Icon={Activity} color="#3b82f6" value={d.protein} unit="g" label="PROTEIN" />
                  <Tile Icon={Wheat} color="#eab308" value={d.carbs} unit="g" label="CARBS" />
                  <Tile Icon={Droplets} color="#f43f5e" value={d.fats} unit="g" label="FATS" />
                </div>
                <div className="inset">
                  <small className="label">HEALTH EVALUATION - <span className={`txt-${d.health_label.toLowerCase()}`}>{d.health_label}</span></small>
                  <p>{d.reasoning}</p>
                  <small className="muted">Fiber {d.fiber}g - Sugar {d.sugar}g</small>
                </div>
              </div>
              {d.alternatives.length > 0 && (
                <div className="card">
                  <small className="label green"><Check size={13} /> SMART AI RECOMMENDATIONS</small>
                  {d.alternatives.map((a, i) => <div className="reco" key={i}><i className="dot" /> {a}</div>)}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
