import { useEffect, useState, ReactElement, useRef } from "react";
import { Navigate } from "react-router-dom";
import { me } from "@/services/auth";
import { useAuthStore } from "@/state/authStore";

export default function RequireAuth({ children }: { children: ReactElement }) {
  const { user, setUser, clear } = useAuthStore();
  const [checking, setChecking] = useState(true);
  const fetchedRef = useRef(false);

  useEffect(() => {
    // Evitar llamadas duplicadas
    if (fetchedRef.current) {
      setChecking(false);
      return;
    }

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

    // Marcar como fetched antes de hacer la llamada
    fetchedRef.current = true;
    
    me()
      .then((u) => setUser(u))
      .catch(() => {
        localStorage.removeItem("token");
        clear();
      })
      .finally(() => setChecking(false));
  }, []); // ✅ Dependencias vacías - solo ejecutar una vez al montar

  if (checking) return <div className="p-6">Cargando…</div>;
  if (!localStorage.getItem("token")) return <Navigate to="/login" replace />;

  return children;
}
