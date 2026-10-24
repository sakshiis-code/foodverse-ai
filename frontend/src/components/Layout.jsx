import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { LayoutDashboard, Scan, Thermometer, ShieldCheck, ChefHat, Calendar, Utensils } from "lucide-react";
import { ping } from "../api.js";

export const NAV = [
  { to: "/", label: "Overview", Icon: LayoutDashboard, end: true },
  { to: "/food-recognition", label: "Food Recognition", Icon: Scan },
  { to: "/freshness-detector", label: "Freshness Detector", Icon: Thermometer },
  { to: "/hygiene-monitor", label: "Hygiene Monitor", Icon: ShieldCheck },
  { to: "/kitchen-assistant", label: "Smart Kitchen", Icon: ChefHat },
  { to: "/meal-planner", label: "Meal Planner", Icon: Calendar },
];

export default function Layout({ children }) {
  const [online, setOnline] = useState(null);
  useEffect(() => {
    ping().then(() => setOnline(true)).catch(() => setOnline(false));
  }, []);

  return (
    <div className="shell">
      <aside className="side">
        <div className="brand"><div className="logo"><Utensils size={18} /></div><span>FoodVerse</span></div>
        <nav>
          {NAV.map(({ to, label, Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => "nav-item" + (isActive ? " on" : "")}>
              {({ isActive }) => (<><Icon size={18} /><span>{label}</span>{isActive && <i className="dot" />}</>)}
            </NavLink>
          ))}
        </nav>
        <div className="status">
          <div className="status-row">
            <span>System Status</span>
            <span className={online === false ? "off" : "on"}><i className="dot" /> {online === null ? "Checking" : online ? "Online" : "Offline"}</span>
          </div>
          <div className="bar"><div style={{ width: online ? "100%" : "15%" }} /></div>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
