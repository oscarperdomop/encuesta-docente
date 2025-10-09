import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import USCOHeader from "@/components/USCOHeader";
import { me } from "@/services/auth";
import { getSurveyQuestions, QuestionRow } from "@/services/catalogs";
import {
  getNextAttempt,
  submitAttempt,
  LikertAnswer,
} from "@/services/attempts";
import { useSelection } from "@/store/selection";
import { loadAttemptExpiry, clearAttemptExpiry } from "@/utils/attemptTimer";

type QRow = QuestionRow & { tipo: "likert" | "texto" };

export default function SurveyStep2() {
  const { attemptId: routeAttemptId } = useParams();
  const nav = useNavigate();
  const { surveyId } = useSelection();

  const [userNombre, setUserNombre] = useState("");
  const [attemptId, setAttemptId] = useState<string | null>(
    routeAttemptId || null
  );
  const [teacherNombre, setTeacherNombre] = useState("—");

  const [expiresAt, setExpiresAt] = useState<Date | null>(null);
  const [leftSec, setLeftSec] = useState<number | null>(null);

  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  const [qsStep1, setQsStep1] = useState<QRow[]>([]); // Q1..Q9
  const [qsStep2, setQsStep2] = useState<QRow[]>([]); // Q10..Q16

  const [vals, setVals] = useState<Record<string, number>>({});
  const [positivos, setPositivos] = useState("");
  const [mejorar, setMejorar] = useState("");
  const [comentarios, setComentarios] = useState("");

  // sesión
  useEffect(() => {
    me()
      .then((u) => setUserNombre(u?.nombre || u?.email || "Usuario"))
      .catch(() => {
        localStorage.removeItem("token");
        nav("/login", { replace: true });
      });
  }, [nav]);

  // resolver attempt activo + cargar teacher + expiry (usa persistido si existe)
  useEffect(() => {
    (async () => {
      if (!surveyId) return;
      const next = await getNextAttempt(surveyId);
      if (!next) {
        alert("No hay intento activo. Regresa a la selección de docentes.");
        nav("/docentes", { replace: true });
        return;
      }

      setTeacherNombre(next.teacher_nombre);

      const currentId =
        routeAttemptId && routeAttemptId === next.attempt_id
          ? routeAttemptId
          : next.attempt_id;

      setAttemptId(currentId);
      if (!routeAttemptId || routeAttemptId !== next.attempt_id) {
        // corrige URL si no coincide
        nav(`/encuesta/${next.attempt_id}/step2`, { replace: true });
      }

      // Timer: primero intenta desde LS (continuación entre pasos), si no, usa el del server
      const persisted = currentId ? loadAttemptExpiry(currentId) : null;
      const exp = persisted
        ? new Date(persisted)
        : next.expires_at
        ? new Date(next.expires_at)
        : null;
      setExpiresAt(exp);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [surveyId, routeAttemptId]);

  // temporizador
  useEffect(() => {
    if (!expiresAt) return;
    const tick = () => {
      const s = Math.max(0, Math.floor((+expiresAt - Date.now()) / 1000));
      setLeftSec(s);
      if (s <= 0) {
        alert("El tiempo del intento terminó.");
        nav("/docentes", { replace: true });
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [expiresAt, nav]);

  // carga de preguntas (Step1: Q1..Q9, Step2: Q10..Q16)
  useEffect(() => {
    (async () => {
      if (!surveyId) return;
      setLoading(true);
      try {
        const all = (await getSurveyQuestions(surveyId)) as QRow[];

        const inRange = (from: number, to: number) => (q: QRow) => {
          const n = Number(q.codigo?.replace(/^Q/i, "") || 0);
          return n >= from && n <= to;
        };

        const step1 = all
          .filter(inRange(1, 9))
          .sort((a, b) => a.orden - b.orden);
        const step2 = all
          .filter(inRange(10, 16))
          .sort((a, b) => a.orden - b.orden);

        setQsStep1(step1);
        setQsStep2(step2);

        // init selects Q10..Q15 + restaurar progreso si existe
        const init: Record<string, number> = {};
        step2
          .filter((q) => q.codigo !== "Q16")
          .forEach((q) => (init[q.id] = 0));

        if (attemptId) {
          const raw = localStorage.getItem(`attempt:${attemptId}:step2`);
          if (raw) {
            const saved = JSON.parse(raw) as {
              vals: Record<string, number>;
              positivos?: string;
              mejorar?: string;
              comentarios?: string;
            };
            setVals({ ...init, ...(saved?.vals || {}) });
            setPositivos(saved?.positivos || "");
            setMejorar(saved?.mejorar || "");
            setComentarios(saved?.comentarios || "");
            return;
          }
        }
        setVals(init);
      } finally {
        setLoading(false);
      }
    })();
  }, [surveyId, attemptId]);

  // autosave local de Step2
  useEffect(() => {
    if (!attemptId) return;
    localStorage.setItem(
      `attempt:${attemptId}:step2`,
      JSON.stringify({ vals, positivos, mejorar, comentarios })
    );
  }, [attemptId, vals, positivos, mejorar, comentarios]);

  // validación de Q10..Q15
  const readyStep2 = useMemo(() => {
    const likerts = qsStep2.filter((q) => q.codigo !== "Q16");
    return likerts.every((q) => {
      const v = vals[q.id] ?? 0;
      return Number.isInteger(v) && v >= 1 && v <= 5;
    });
  }, [qsStep2, vals]);

  const setVal = (qid: string, v: number) =>
    setVals((p) => ({ ...p, [qid]: v }));

  async function onSubmit() {
    if (!attemptId) return;

    // Validar Step1 completo (Q1..Q9) desde LS
    const rawStep1 = localStorage.getItem(`attempt:${attemptId}:step1`);
    const step1Vals: Record<string, number> = rawStep1
      ? JSON.parse(rawStep1)
      : {};
    const readyStep1 = qsStep1.every((q) => {
      const v = step1Vals[q.id] ?? 0;
      return Number.isInteger(v) && v >= 1 && v <= 5;
    });

    if (!readyStep1) {
      alert(
        "Faltan respuestas del Paso 1 (Q1–Q9). Regresa y completa antes de enviar."
      );
      return;
    }
    if (!readyStep2) {
      alert(
        "Responde todas las preguntas del Paso 2 (Q10–Q15) antes de enviar."
      );
      return;
    }
    if (!window.confirm("¿Desea terminar la encuesta?")) return;

    try {
      setSending(true);

      // Construir 15 respuestas (Q1..Q15) con clave `value`
      const a1: LikertAnswer[] = qsStep1.map((q) => ({
        question_id: q.id,
        value: Number(step1Vals[q.id]),
      }));
      const a2: LikertAnswer[] = qsStep2
        .filter((q) => q.codigo !== "Q16")
        .map((q) => ({ question_id: q.id, value: Number(vals[q.id]) }));

      const answers: LikertAnswer[] = [...a1, ...a2];

      await submitAttempt(attemptId, answers, {
        positivos: (positivos || "").trim(),
        mejorar: (mejorar || "").trim(),
        comentarios: (comentarios || "").trim(),
      });

      // limpiar progreso y expiry de este attempt
      localStorage.removeItem(`attempt:${attemptId}:step1`);
      localStorage.removeItem(`attempt:${attemptId}:step2`);
      clearAttemptExpiry(attemptId);

      // Avanzar al siguiente o ir a resumen
      if (!surveyId) return nav("/docentes", { replace: true });
      const next = await getNextAttempt(surveyId);
      if (next?.attempt_id) {
        nav(`/encuesta/${next.attempt_id}/step1`, { replace: true });
      } else {
        nav("/resumen", { replace: true });
      }
    } catch (e: any) {
      const detail =
        e?.response?.data?.detail ||
        e?.response?.data?.message ||
        "No se pudo enviar. Intenta nuevamente.";
      alert(detail);
    } finally {
      setSending(false);
    }
  }

  const fmtTimer = (s: number | null) =>
    s === null
      ? "—:—"
      : `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(
          s % 60
        ).padStart(2, "0")}`;

  return (
    <div className="min-h-screen bg-usco-bg">
      <USCOHeader subtitle="Encuesta Docente · Paso 2/2" />
      <main className="max-w-5xl mx-auto px-4 md:px-6 py-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <b>{userNombre}</b> · Docente actual: <b>{teacherNombre}</b>
          </div>
          <div className="text-sm text-gray-700">
            Tiempo restante:{" "}
            <span className="font-mono">{fmtTimer(leftSec)}</span>
          </div>
        </div>

        {loading ? (
          <div className="text-center text-gray-500 py-10">Cargando…</div>
        ) : (
          <div className="space-y-8">
            <Section title="USO DE MATERIALES PARA EL DESARROLLO DEL CURSO">
              {qsStep2
                .filter((q) => {
                  const n = Number(q.codigo.replace(/^Q/i, ""));
                  return n >= 10 && n <= 11;
                })
                .map((q) => (
                  <LikertItem
                    key={q.id}
                    label={`${q.codigo}. ${
                      q.enunciado || "Enunciado (reemplazar)"
                    }`}
                    value={vals[q.id] ?? 0}
                    onChange={(v) => setVal(q.id, v)}
                  />
                ))}
            </Section>

            <Section title="EVALUACIÓN DEL CONOCIMIENTO">
              {qsStep2
                .filter((q) => {
                  const n = Number(q.codigo.replace(/^Q/i, ""));
                  return n >= 12 && n <= 13;
                })
                .map((q) => (
                  <LikertItem
                    key={q.id}
                    label={`${q.codigo}. ${
                      q.enunciado || "Enunciado (reemplazar)"
                    }`}
                    value={vals[q.id] ?? 0}
                    onChange={(v) => setVal(q.id, v)}
                  />
                ))}
            </Section>

            <Section title="MICRODISEÑO DEL CURSO Y BIBLIOGRAFÍA">
              {qsStep2
                .filter((q) => {
                  const n = Number(q.codigo.replace(/^Q/i, ""));
                  return n >= 14 && n <= 15;
                })
                .map((q) => (
                  <LikertItem
                    key={q.id}
                    label={`${q.codigo}. ${
                      q.enunciado || "Enunciado (reemplazar)"
                    }`}
                    value={vals[q.id] ?? 0}
                    onChange={(v) => setVal(q.id, v)}
                  />
                ))}
            </Section>

            <Section title="OBSERVACIONES (opcional)">
              <Textarea
                label="Aspectos positivos"
                value={positivos}
                onChange={setPositivos}
              />
              <Textarea
                label="Aspectos por mejorar"
                value={mejorar}
                onChange={setMejorar}
              />
              <Textarea
                label="Comentarios generales"
                value={comentarios}
                onChange={setComentarios}
              />
            </Section>

            <div className="flex justify-between items-center">
              <button
                className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200"
                onClick={() => nav(-1)}
              >
                Regresar
              </button>
              <button
                disabled={!readyStep2 || sending || qsStep2.length === 0}
                className="px-5 py-2 rounded-xl bg-usco-primary text-white disabled:opacity-60"
                onClick={onSubmit}
              >
                {sending ? "Enviando…" : "Enviar"}
              </button>
            </div>
          </div>
        )}
      </main>

      <p className="text-center text-gray-500 mt-6 text-sm">
        © USCO — Prototipo para demostración
      </p>
    </div>
  );
}

/* ---------- UI helpers ---------- */
function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="bg-white rounded-2xl shadow-card p-5 md:p-6">
      <h2 className="font-semibold text-lg md:text-xl mb-3">{title}</h2>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

function LikertItem({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="bg-gray-50 rounded-xl p-4">
      <div className="mb-2 font-medium">{label}</div>
      <select
        className="border rounded-xl p-2 outline-none focus:ring-2 focus:ring-usco-primary/30 focus:border-usco-primary"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      >
        <option value={0}>Seleccionar</option>
        {[1, 2, 3, 4, 5].map((n) => (
          <option key={n} value={n}>
            {n}
          </option>
        ))}
      </select>
    </div>
  );
}

function Textarea({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="bg-gray-50 rounded-xl p-4">
      <div className="mb-2 font-medium">{label}</div>
      <textarea
        className="w-full min-h-[120px] border rounded-xl p-3 outline-none focus:ring-2 focus:ring-usco-primary/30 focus:border-usco-primary"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
