import { useEffect, useMemo, useRef, useState } from "react";
import { Upload, Mic, Square, X, AlertCircle } from "lucide-react";
import { post } from "../api.js";

/* ---- send a request and track loading / error / result ---- */
export function useAnalyze(path, asJson = false) {
  const [s, set] = useState({ loading: false, error: "", data: null });
  const run = async (body) => {
    set({ loading: true, error: "", data: null });
    try {
      set({ loading: false, error: "", data: await post(path, body, asJson) });
    } catch (e) {
      set({ loading: false, error: e.message, data: null });
    }
  };
  return [s, run];
}

/* ---- microphone recording ---- */
export function useRecorder() {
  const recorder = useRef(null);
  const chunks = useRef([]);
  const [recording, setRecording] = useState(false);
  const [blob, setBlob] = useState(null);
  const [err, setErr] = useState("");

  async function start() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks.current = [];
      const r = new MediaRecorder(stream);
      r.ondataavailable = (e) => chunks.current.push(e.data);
      r.onstop = () => {
        setBlob(new Blob(chunks.current, { type: r.mimeType || "audio/webm" }));
        stream.getTracks().forEach((t) => t.stop());
      };
      r.start();
      recorder.current = r;
      setRecording(true);
      setErr("");
    } catch {
      setErr("Microphone not available");
    }
  }
  function stop() {
    if (recorder.current && recorder.current.state !== "inactive") recorder.current.stop();
    setRecording(false);
  }
  return { recording, blob, err, start, stop, clear: () => setBlob(null) };
}

export const voiceFile = (blob) => new File([blob], "voice.webm", { type: blob.type || "audio/webm" });

export function MicButton({ rec, hold = true, idle = "HOLD TO RECORD" }) {
  const label = rec.err || (rec.recording ? "RECORDING..." : rec.blob ? "VOICE NOTE SAVED" : idle);
  const handlers = hold
    ? { onMouseDown: rec.start, onMouseUp: rec.stop, onMouseLeave: () => rec.recording && rec.stop(),
        onTouchStart: rec.start, onTouchEnd: rec.stop }
    : { onClick: () => (rec.recording ? rec.stop() : rec.start()) };
  return (
    <div className="mic-wrap">
      <button type="button" className={"mic" + (rec.recording ? " live" : "")} {...handlers} aria-label="Record voice note">
        <span className="circle sm">{rec.recording && !hold ? <Square size={16} /> : <Mic size={18} />}</span>
        <small>{label}</small>
      </button>
      {rec.blob && !rec.recording && (
        <button type="button" className="clear" onClick={rec.clear}>Remove voice note</button>
      )}
    </div>
  );
}

/* ---- drag & drop upload with preview ---- */
export function UploadBox({ file, onFile, accept = "image/*", title, hint, Icon = Upload, tall, dark }) {
  const input = useRef(null);
  const [over, setOver] = useState(false);
  const url = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => () => url && URL.revokeObjectURL(url), [url]);
  const pick = (f) => f && onFile(f);

  return (
    <div className={`drop${over ? " over" : ""}${tall ? " tall" : ""}${dark ? " dark" : ""}`}
      onClick={() => !file && input.current.click()}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); pick(e.dataTransfer.files[0]); }}>
      <input ref={input} type="file" accept={accept} hidden onChange={(e) => pick(e.target.files[0])} />
      {file ? (
        <>
          {file.type.startsWith("video/") ? <video src={url} controls /> : <img src={url} alt="Selected file preview" />}
          <button type="button" className="x" aria-label="Remove file" onClick={(e) => { e.stopPropagation(); onFile(null); }}><X size={16} /></button>
        </>
      ) : (
        <div className="drop-empty">
          <div className="circle"><Icon size={26} /></div>
          <b>{title}</b>
          <span>{hint}</span>
        </div>
      )}
    </div>
  );
}

export const Placeholder = ({ Icon, title, text }) => (
  <div className="placeholder"><Icon size={56} strokeWidth={1.2} /><h3>{title}</h3><p>{text}</p></div>
);

export const ErrorBox = ({ message }) => (
  <div className="errorbox"><AlertCircle size={18} /><div><b>Something went wrong.</b><br />{message}</div></div>
);

export const scoreColor = (v) => (v >= 75 ? "var(--green)" : v >= 50 ? "var(--amber)" : "var(--red)");

export function Ring({ value }) {
  const r = 26, c = 2 * Math.PI * r;
  return (
    <div className="ring" title="Health score">
      <svg width="64" height="64" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r={r} fill="none" stroke="var(--line)" strokeWidth="5" />
        <circle cx="32" cy="32" r={r} fill="none" stroke={scoreColor(value)} strokeWidth="5" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - value / 100)} transform="rotate(-90 32 32)" />
      </svg>
      <div><b>{value}</b><small>SCORE</small></div>
    </div>
  );
}

export const Bar = ({ value }) => (
  <div className="minibar"><div style={{ width: `${Math.max(0, Math.min(100, value))}%`, background: scoreColor(value) }} /></div>
);

export const Tile = ({ Icon, color, value, unit = "", label }) => (
  <div className="tile">
    <div className="tile-icon" style={{ color, background: color + "22" }}><Icon size={18} /></div>
    <div><b>{value}{unit}</b><small>{label}</small></div>
  </div>
);
