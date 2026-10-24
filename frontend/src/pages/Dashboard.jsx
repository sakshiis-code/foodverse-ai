import { Link } from "react-router-dom";
import { Scan, Thermometer, ShieldCheck, ChefHat, Calendar, ArrowRight } from "lucide-react";

const CARDS = [
  { to: "/food-recognition", title: "Food Recognition", text: "Identify dishes & nutrition", Icon: Scan, color: "#10b981" },
  { to: "/freshness-detector", title: "Freshness Detector", text: "Detect spoilage instantly", Icon: Thermometer, color: "#f97316" },
  { to: "/hygiene-monitor", title: "Hygiene Monitor", text: "Kitchen compliance AI", Icon: ShieldCheck, color: "#3b82f6" },
  { to: "/kitchen-assistant", title: "Smart Kitchen", text: "Real-time cooking aid", Icon: ChefHat, color: "#8b5cf6" },
  { to: "/meal-planner", title: "Meal Planner", text: "Personalized diet plans", Icon: Calendar, color: "#06b6d4" },
];

export default function Dashboard() {
  return (
    <div className="page">
      <section className="hero">
        <h1>Welcome to <span>FoodVerse AI</span></h1>
        <p>A unified multimodal AI platform revolutionizing the food lifecycle from farm to fork.</p>
        <Link to="/food-recognition" className="pill">Real-time Analysis</Link>
      </section>
      <div className="cards">
        {CARDS.map(({ to, title, text, Icon, color }) => (
          <Link key={to} to={to} className="mod-card">
            <div className="mod-icon" style={{ background: color }}><Icon size={22} color="#fff" /></div>
            <b>{title}</b>
            <span>{text}</span>
            <small className="launch">LAUNCH MODULE <ArrowRight size={12} /></small>
          </Link>
        ))}
      </div>
    </div>
  );
}
