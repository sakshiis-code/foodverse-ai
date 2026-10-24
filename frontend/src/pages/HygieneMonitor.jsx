import { useState } from "react";
import { ShieldCheck, Video, Eye, FileText, Download, MapPin } from "lucide-react";
import { PATHS } from "../api.js";
import { UploadBox, useAnalyze, ErrorBox, Bar } from "../components/ui.jsx";

export default function HygieneMonitor() {
  const [file, setFile] = useState(null);
  const [rules, setRules] = useState("Gloves mandatory. Hairnets required. No phone use.");
  const [s, run] = useAnalyze(PATHS.hygiene);
  const d = s.data;

  const submit = () => {
    const f = new FormData();
    f.append("file", file);
    f.append("notes", rules);
    run(f);
  };

  const download = () => {
    const lines = [
      "FoodVerse AI - Hygiene Report", "",
      `Compliance score: ${d.compliance_score}/100 (${d.grade})`, `Floor cleanliness: ${d.floor_score}/100`, "",
      "Summary:", d.summary, "", "Violations:",
      ...d.violations.map((v) => `- [${v.severity}] ${v.violation} (${v.location}): ${v.reason}`), "",
      "Recommendations:", ...d.recommendations.map((r) => `- ${r}`),
    ];
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/plain" }));
    a.download = "hygiene-report.txt";
    a.click();
  };

  return (
    <div className="page">
      <div className="head-row">
        <div>
          <h1 className="title"><ShieldCheck size={24} color="#3b82f6" /> Hygiene & Safety Monitor</h1>
          <p className="sub">AI-powered surveillance for kitchen compliance and safety risks.</p>
        </div>
        {d && <button className="btn ghost" onClick={download}><Download size={15} /> Download Report</button>}
      </div>
      <div className="grid-hyg">
        <div className="stack">
          <UploadBox file={file} onFile={setFile} accept="image/*,video/*" Icon={Video} dark tall
            title="Upload CCTV Footage or Image" hint="Photo or video, up to 50 MB" />
          <div className="card">
            <small className="label"><FileText size={13} /> COMPLIANCE RULES</small>
            <textarea className="rules" value={rules} onChange={(e) => setRules(e.target.value)} />
          </div>
          <button className="btn blue" disabled={!file || s.loading} onClick={submit}>{s.loading ? "Inspecting..." : "Run AI Inspection"}</button>
        </div>

        <aside className="card insights">
          <h3 className="live">LIVE INSIGHTS <i className="dot" /></h3>
          {s.error && <ErrorBox message={s.error} />}
          {!d && !s.error && (
            <div className="placeholder small"><Eye size={40} strokeWidth={1.2} />
              <p>{s.loading ? "Inspecting footage..." : "Monitoring Inactive. Upload footage to start analysis."}</p></div>)}
          {d && (
            <>
              <div className="two">
                <div className="score-tile"><b>{d.compliance_score}</b><small>OVERALL SCORE</small><Bar value={d.compliance_score} /></div>
                <div className="score-tile"><b>{d.floor_score}</b><small>FLOOR CLEANLINESS</small><Bar value={d.floor_score} /></div>
              </div>
              <small className="label">REAL-TIME ALERTS</small>
              {d.violations.length === 0 && <p className="muted">No violations detected.</p>}
              {d.violations.map((v, i) => (
                <div className="alert" key={i}>
                  <div className="alert-top"><b>{v.violation}</b><span className={`sev ${v.severity.toLowerCase()}`}>{v.severity.toUpperCase()}</span></div>
                  {v.location && <small className="muted"><MapPin size={11} /> {v.location}</small>}
                  <blockquote>{v.reason}</blockquote>
                </div>
              ))}
              <div className="summary"><small className="label blue">AI SUMMARY</small><p>{d.summary}</p>
                {d.recommendations.length > 0 && <ul>{d.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul>}
              </div>
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
