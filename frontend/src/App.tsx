import { useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import PublicLayout from "./layouts/PublicLayout";
import DashboardLayout from "./layouts/DashboardLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import ModeSelection from "./pages/ModeSelection";
import ExerciseSelection from "./pages/ExerciseSelection";
import CameraSetup from "./pages/CameraSetup";
import StsLiveSessionPage from "./pages/sts/StsLiveSessionPage";
import SlsLiveSessionPage from "./pages/sls/SlsLiveSessionPage";
import WbltLiveSessionPage from "./pages/wblt/WbltLiveSessionPage";
import Report from "./pages/Report";
import SessionHistory from "./pages/SessionHistory";
import Reminders from "./pages/Reminders";
import Profile from "./pages/Profile";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    if (!window.location.hash) window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <Routes>
        <Route element={<PublicLayout />}>
          <Route index element={<Landing />} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
        </Route>
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="mode" element={<ModeSelection />} />
            <Route path="exercise" element={<ExerciseSelection />} />
            <Route path="camera" element={<CameraSetup />} />
            <Route path="sts/live" element={<StsLiveSessionPage />} />
            <Route path="sls/live" element={<SlsLiveSessionPage />} />
            <Route path="wblt/live" element={<WbltLiveSessionPage />} />
            <Route path="report" element={<Report />} />
            <Route path="history" element={<SessionHistory />} />
            <Route path="reminders" element={<Reminders />} />
            <Route path="profile" element={<Profile />} />
          </Route>
        </Route>
        <Route path="*" element={<Landing />} />
      </Routes>
    </BrowserRouter>
  );
}
