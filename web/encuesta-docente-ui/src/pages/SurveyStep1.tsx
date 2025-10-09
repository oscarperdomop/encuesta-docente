import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import USCOHeader from "@/components/USCOHeader";
import { getSurveyQuestions, QuestionRow } from "@/services/catalogs";
import { getNextAttempt } from "@/services/attempts";
import { useSelection } from "@/store/selection";
import { me } from "@/services/auth";
import { saveAttemptExpiry } from "@/utils/attemptTimer";

type Answers = Record<string, number>;

export default function SurveyStep1() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const nav = useNavigate();
  const { surveyId } = useSelection();

  const [userNombre, setUserNombre] = useState("");
  const [teacherNombre, setTeacherNombre] = useState("—");
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);
  const [leftSec, setLeftSec] = useState<number | null>(null);

  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState<QuestionRow[]>([]);
  const [answers, setAnswers] = useState<Answers>({});

  const LS_KEY = `attempt:${attemptId}:step1`;

  useEffect(() => {
    me()
      .then((u) => setUserNombre(u?.nombre || u?.email || "Usuario"))
      .catch(() => {
        localStorage.removeItem("token");
        nav("/login", { replace: true });
      });
  }, [nav]);

  useEffect(() => {
    if (!attemptId || !surveyId) return;
    (async () => {
      try {
        setLoading(true);

        const next = await getNextAttempt(surveyId);
        if (!next) {
          alert("No hay intento activo. Regresando a docentes.");
          nav("/docentes", { replace: true });
          return;
        }
        if (next.attempt_id !== attemptId) {
          nav(`/encuesta/${next.attempt_id}/step1`, { replace: true });
          return;
        }

        setTeacherNombre(next.teacher_nombre);
        setExpiresAt(next.expires_at ? new Date(next.expires_at) : null);

        // >>> GUARDA el expiry para que Step 2 continúe el conteo
        saveAttemptExpiry(next.attempt_id, next.expires_at || null);

        const all = await getSurveyQuestions(surveyId);
        const step1 = all
          .filter((q) => q.orden <= 9)
          .sort((a, b) => a.orden - b.orden);
        setQuestions(step1);

        const raw = localStorage.getItem(LS_KEY);
        if (raw) setAnswers(JSON.parse(raw) as Answers);
      } finally {
        setLoading(false);
      }
    })();
  }, [attemptId, surveyId, nav]);

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

  useEffect(() => {
    if (attemptId) localStorage.setItem(LS_KEY, JSON.stringify(answers));
  }, [answers, attemptId]);

  const bySection = useMemo(() => {
    const groups = new Map<string, QuestionRow[]>();
    for (const q of questions) {
      if (!groups.has(q.section)) groups.set(q.section, []);
      groups.get(q.section)!.push(q);
    }
    return Array.from(groups.entries());
  }, [questions]);

  const allAnswered = useMemo(
    () =>
      !!questions.length &&
      questions.every(
        (q) => (answers[q.id] ?? 0) >= 1 && (answers[q.id] ?? 0) <= 5
      ),
    [questions, answers]
  );

  function setAnswer(qid: string, value: number) {
    setAnswers((p) => ({ ...p, [qid]: value }));
  }

  const fmtTimer = (s: number | null) =>
    s === null
      ? "—:—"
      : `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(
          s % 60
        ).padStart(2, "0")}`;

  return (
    <div className="min-h-screen bg-usco-bg">
      <USCOHeader subtitle="Encuesta Docente · Paso 1/2" />
      <main className="max-w-5xl mx-auto px-4 md:px-6 py-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
          <div className="text-sm text-gray-700">
            <b>{userNombre}</b> · Docente actual: <b>{teacherNombre}</b>
          </div>
          <div className="text-sm text-gray-700">
            Tiempo restante:{" "}
            <span className="font-mono">{fmtTimer(leftSec)}</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-card p-4 md:p-6">
          {loading ? (
            <div className="text-gray-500">Cargando…</div>
          ) : (
            <>
              {bySection.map(([title, items]) => (
                <section key={title} className="mb-6">
                  <h2 className="font-semibold text-lg mb-3">{title}</h2>
                  <div className="space-y-3">
                    {items.map((q) => (
                      <div
                        key={q.id}
                        className="p-3 rounded-xl bg-gray-50 border border-gray-100"
                      >
                        <div className="mb-2">
                          <span className="text-gray-500 mr-2">
                            {q.codigo}.
                          </span>
                          {q.enunciado}
                        </div>
                        <select
                          className="border rounded-xl p-2 outline-none focus:ring-2 focus:ring-usco-primary/30 focus:border-usco-primary"
                          value={answers[q.id] ?? 0}
                          onChange={(e) =>
                            setAnswer(q.id, Number(e.target.value))
                          }
                        >
                          <option value={0}>Seleccionar</option>
                          {[1, 2, 3, 4, 5].map((n) => (
                            <option key={n} value={n}>
                              {n}
                            </option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                </section>
              ))}

              <div className="flex justify-between pt-2">
                <button
                  className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200"
                  onClick={() => nav("/docentes")}
                >
                  Regresar
                </button>
                <button
                  disabled={!allAnswered}
                  className="px-5 py-2 rounded-xl bg-usco-primary text-white disabled:opacity-60"
                  onClick={() => nav(`/encuesta/${attemptId}/step2`)}
                >
                  Siguiente
                </button>
              </div>
            </>
          )}
        </div>

        <p className="text-center text-gray-500 mt-6 text-sm">
          © USCO — Prototipo para demostración
        </p>
      </main>
    </div>
  );
}
