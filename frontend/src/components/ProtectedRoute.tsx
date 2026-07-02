import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth";

export default function ProtectedRoute() {
  const { token, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="center muted" style={{ padding: 48 }}>
        Loading...
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
