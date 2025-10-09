import { useEffect, useState, ReactElement } from "react";
import { Navigate } from "react-router-dom";
import { me } from "@/services/auth";
import { useAuthStore } from "@/state/authStore";

export default function RequireAuth({ children }: { children: ReactElement }) {
  const { user, setUser, clear } = useAuthStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      clear();
      setChecking(false);
      return;
    }
    if (user) {
      setChecking(false);
      return;
    }
    me()
      .then((u) => setUser(u))
      .catch(() => {
        localStorage.removeItem("token");
        clear();
      })
      .finally(() => setChecking(false));
  }, [user, setUser, clear]);

  if (checking) return <div className="p-6">Cargando…</div>;
  if (!localStorage.getItem("token")) return <Navigate to="/login" replace />;

  return children;
}
