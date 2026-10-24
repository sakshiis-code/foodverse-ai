import { useState } from "react";
import { Search, Thermometer, Info, AlertCircle, Lightbulb } from "lucide-react";
import { PATHS } from "../api.js";
import { UploadBox, MicButton, useRecorder, voiceFile, useAnalyze, Placeholder, ErrorBox } from "../components/ui.jsx";

export default function FreshnessDetector() {
  const [file, setFile] = useState(null);
  const [time, setTime] = useState("");
  const [type, setType] = useState("Room Temp");
  const rec = useRecorder();
  const [s, run] = useAnalyze(PATHS.freshness);

  const submit = () => {
    const f = new FormData();
    f.append("file", file);
    f.append("storage_type", type);
    if (time.trim()) f.append("storage_time", time.trim());
    if (rec.blob) f.append("audio_file", voiceFile(rec.blob));
    run(f);
  };
  const d = s.data;
  const lvl = d ? d.freshness_level.toLowerCase() : "";

  return (
    <div className="page">
      <h1 className="title"><Thermometer size={26} color="#f97316" /> AI Freshness Detector</h1>
      <p className="sub">Detect spoilage early using multimodal vision & sensory analysis.</p>
      <div className="grid2">
        <div className="stack">
          <div className="card">
            <h3 className="h3">1. Visual Check</h3>
            <UploadBox file={file} onFile={setFile} Icon={Search} title="Upload Photo of Food" hint="Drag & drop or click to browse" />
          </div>
          <div className="card">
            <h3 className="h3">2. Context & Sensory Data <Info size={14} className="muted" /></h3>
            <div className="two">
              <label className="field"><small>STORED FOR</small><input value={time} onChange={(e) => setTime(e.target.value)} placeholder="e.g. 3 days" /></label>
              <label className="field"><small>STORAGE TYPE</small>
                <select value={type} onChange={(e) => setType(e.target.value)}><option>Room Temp</option><option>Fridge</option><option>Freezer</option></select>
              </label>
            </div>
            <small className="label">DESCRIBE SMELL / TEXTURE (OPTIONAL)</small>
            <MicButton rec={rec} hold={false} idle="Tap mic to add voice notes" />
          </div>
          <button className="btn orange" disabled={!file || s.loading} onClick={submit}>{s.loading ? "Checking..." : "Check Freshness"}</button>
        </div>

        <div className="stack">
          {s.error && <ErrorBox message={s.error} />}
          {!d && !s.error && <Placeholder Icon={Thermometer} title={s.loading ? "Checking your food..." : "Ready to Analyze"} text="Upload an image and provide context to get a multimodal freshness report." />}
          {d && (
            <div className="card center">
              <span className="pill dim">DETECTION RESULT</span>
              <h2 className="dish big">{d.item_name}</h2>
              <p><span className={`badge ${lvl}`}><AlertCircle size={13} /> {d.freshness_level}</span> <small className="muted">Confidence: {d.confidence}%</small></p>
              <div className={`safety ${lvl}`}><small>SAFETY STATUS</small><b>{d.safety_status.toUpperCase()}</b></div>
              {d.detected_signs.length > 0 && (
                <div className="inset left"><small className="label">DETECTED SIGNS</small>
                  <div className="chips">{d.detected_signs.map((x, i) => <span className="chip" key={i}>{x}</span>)}</div>
                </div>)}
              <div className="inset left"><small className="label">AI REASONING</small><p>{d.reasoning}</p></div>
              <p className="advice"><Lightbulb size={14} /> Advice: {d.recommendation}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
