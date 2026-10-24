import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import FoodRecognition from "./pages/FoodRecognition.jsx";
import FreshnessDetector from "./pages/FreshnessDetector.jsx";
import HygieneMonitor from "./pages/HygieneMonitor.jsx";
import KitchenAssistant from "./pages/KitchenAssistant.jsx";
import MealPlanner from "./pages/MealPlanner.jsx";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/food-recognition" element={<FoodRecognition />} />
        <Route path="/freshness-detector" element={<FreshnessDetector />} />
        <Route path="/hygiene-monitor" element={<HygieneMonitor />} />
        <Route path="/kitchen-assistant" element={<KitchenAssistant />} />
        <Route path="/meal-planner" element={<MealPlanner />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
