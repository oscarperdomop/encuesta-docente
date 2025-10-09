// src/pages/ResumenTurno.tsx
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import USCOHeader from "@/components/USCOHeader";
import { me, logout } from "@/services/auth";
import {
  getNextAttempt,
  getAttemptsSummary,
  AttemptsSummary,
} from "@/services/attempts";
import { useSelection } from "@/store/selection";
import api from "@/services/api";

export default function ResumenTurno() {
  const nav = useNavigate();
  const { surveyId } = useSelection();

  const [userNombre, setUserNombre] = useState("Usuario");
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<AttemptsSummary | null>(null);
  const [hasNext, setHasNext] = useState(false);

  // sesión
  useEffect(() => {
    me()
      .then((u) => setUserNombre(u?.nombre || u?.email || "Usuario"))
      .catch(() => {
        localStorage.removeItem("token");
        nav("/login", { replace: true });
      });
  }, [nav]);

  // datos
  useEffect(() => {
    (async () => {
      if (!surveyId) return;
      setLoading(true);
      try {
        const s = await getAttemptsSummary(surveyId);
        setSummary(s);
        const next = await getNextAttempt(surveyId);
        setHasNext(!!next);
      } finally {
        setLoading(false);
      }
    })();
  }, [surveyId]);

  // contadores (fallback si API cambia nombres o items viene vacío)
  const counts = useMemo(() => {
    const base = { enviados: 0, en_progreso: 0, pendientes: 0 };
    if (!summary) return base;

    // si la API ya trae totales confiables, úsalos
    if (
      typeof summary.enviados === "number" ||
      typeof summary.en_progreso === "number" ||
      typeof summary.pendientes === "number"
    ) {
      return {
        enviados: summary.enviados ?? 0,
        en_progreso: summary.en_progreso ?? 0,
        pendientes: summary.pendientes ?? 0,
      };
    }

    // fallback: cuenta por estados en items
    const c = { ...base };
    for (const it of summary.items || []) {
      if (it.estado === "enviado") c.enviados++;
      else if (it.estado === "en_progreso") c.en_progreso++;
      else c.pendientes++;
    }
    return c;
  }, [summary]);

  async function onFinish() {
    try {
      // opcional: que el backend invalide el token/registro de sesión
      await api
        .post("/sessions/close", { survey_id: surveyId })
        .catch(() => {});
    } finally {
      await logout({ server: true });
      // hard redirect (evita volver con “atrás”)
      location.replace("/login");
    }
  }
  const canFinish = useMemo(() => {
    if (!summary) return !hasNext;
    if (typeof summary.can_finish === "boolean") return summary.can_finish;
    return counts.pendientes === 0 && counts.en_progreso === 0;
  }, [summary, hasNext, counts]);

  return (
    <div className="min-h-screen bg-usco-bg">
      <USCOHeader subtitle="Encuesta Docente · Resumen de turno" />

      <main className="max-w-5xl mx-auto px-4 md:px-6 py-6">
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm text-gray-700">
            <b>{userNombre}</b>
          </div>
          <div className="text-sm text-gray-700">
            Enviados: <b>{counts.enviados}</b> · En progreso:{" "}
            <b>{counts.en_progreso}</b> · Pendientes: <b>{counts.pendientes}</b>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-card p-5">
          {loading ? (
            <div className="text-center text-gray-500 py-8">Cargando…</div>
          ) : summary && summary.items && summary.items.length > 0 ? (
            <ul className="space-y-2">
              {summary.items.map((it) => (
                <li
                  key={it.teacher_id}
                  className="flex items-center justify-between p-3 rounded-xl bg-gray-50"
                >
                  <span className="font-medium">{it.teacher_nombre}</span>
                  <span
                    className={`px-2 py-1 rounded-full text-xs ${
                      it.estado === "enviado"
                        ? "bg-green-100 text-green-700"
                        : it.estado === "en_progreso"
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {it.estado}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center text-gray-600">
              No hay más docentes en la cola. ¡Has terminado!
            </div>
          )}

          <div className="flex justify-end gap-3 mt-6">
            {hasNext && (
              <button
                className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200"
                onClick={() => nav(-1)}
              >
                Ir al siguiente pendiente
              </button>
            )}
            <button
              className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200"
              onClick={() => nav("/docentes")}
            >
              Volver a la lista
            </button>
            <button
              disabled={!canFinish}
              className="px-5 py-2 rounded-xl bg-usco-primary text-white disabled:opacity-60"
              onClick={onFinish}
            >
              Finalizar turno
            </button>
          </div>
        </div>

        <p className="text-center text-gray-500 mt-6 text-sm">
          © USCO — Prototipo para demostración
        </p>
      </main>
    </div>
  );
}
