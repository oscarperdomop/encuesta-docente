import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { me } from "@/services/auth";

export default function ProtectedRoute({
  children,
}: {
  children: React.ReactNode;
}) {
  const nav = useNavigate();
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    let alive = true;

    const ensure = async () => {
      const t = localStorage.getItem("token");
      if (!t) {
        if (alive) setOk(false);
        nav("/login", { replace: true });
        return;
      }
      try {
        await me(); // valida en servidor
        if (alive) setOk(true);
      } catch {
        localStorage.removeItem("token");
        sessionStorage.clear();
        if (alive) setOk(false);
        nav("/login", { replace: true });
      }
    };

    ensure();

    // ← cierres de sesión en otras pestañas
    const onStorage = (e: StorageEvent) => {
      if (e.key === "__logout__") nav("/login", { replace: true });
    };
    window.addEventListener("storage", onStorage);

    // ← si la página vuelve desde BFCache tras logout, recarga a /login
    const onPageShow = (e: PageTransitionEvent) => {
      if ((e as any).persisted && !localStorage.getItem("token")) {
        location.replace("/login");
      }
    };
    window.addEventListener("pageshow", onPageShow);

    return () => {
      alive = false;
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("pageshow", onPageShow);
    };
  }, [nav]);

  // loader mientras validamos sesión
  if (ok === null)
    return <div className="p-6 text-center text-gray-500">Cargando…</div>;
  if (!ok) return null;
  return <>{children}</>;
}
