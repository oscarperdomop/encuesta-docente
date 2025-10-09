import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import USCOHeader from "@/components/USCOHeader";
import USCOPage from "@/components/USCOPage";
import { getAttempt, submitAttempt, getNextAttempt } from "@/services/attempts";
import { getSurveyQuestions, Question } from "@/services/questions";
import LikertSelect from "@/components/LikertSelect";
import { getActiveSurveyId } from "@/store/survey";

type VLikert = Record<string, number | "">;
type VObs = { positivos?: string; mejorar?: string; comentarios?: string };

export default function Step2() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const nav = useNavigate();
  const surveyId = getActiveSurveyId();

  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [values, setValues] = useState<VLikert>({});
  const [obs, setObs] = useState<VObs>({});
  const [teacherName, setTeacherName] = useState<string>("");

  const qsStep2 = useMemo(
    () =>
      questions
        .filter((q) => /^Q1[0-6]$/.test(q.codigo))
        .sort((a, b) => a.orden - b.orden),
    [questions]
  );

  // Q16 (texto) si existe
  const q16 = useMemo(
    () => questions.find((q) => q.codigo === "Q16"),
    [questions]
  );

  const allAnswered = useMemo(
    () =>
      qsStep2.length > 0 &&
      qsStep2.every((q) => typeof values[q.id] === "number"),
    [qsStep2, values]
  );

  useEffect(() => {
    if (!attemptId || !surveyId) return;
    (async () => {
      try {
        setLoading(true);
        const [att, qs] = await Promise.all([
          getAttempt(attemptId),
          getSurveyQuestions(surveyId),
        ]);
        setQuestions(qs);
        setTeacherName(
          att?.teacher_id ? `Docente ${att.teacher_id.slice(0, 8)}…` : ""
        );

        // Pre-carga (si hubiera)
        const likert: VLikert = {};
        for (const q of qs.filter((x) => /^Q1[0-6]$/.test(x.codigo))) {
          likert[q.id] = "";
        }
        for (const a of att.answers || []) {
          if (a.value && a.question_id && likert[a.question_id] !== undefined) {
            likert[a.question_id] = a.value;
          }
        }
        setValues(likert);

        if (q16) {
          const a16 = (att.answers || []).find(
            (a) => a.question_id === q16.id && a.texto
          );
          setObs(a16?.texto || { positivos: "", mejorar: "", comentarios: "" });
        }
      } finally {
        setLoading(false);
      }
    })();
  }, [attemptId, surveyId, q16?.id]);

  async function onSubmit() {
    if (!attemptId) return;
    const answers = qsStep2.map((q) => ({
      question_id: q.id,
      value: Number(values[q.id]),
    }));
    const payload: any = { answers };
    if (q16) {
      const hasText =
        (obs.positivos && obs.positivos.trim()) ||
        (obs.mejorar && obs.mejorar.trim()) ||
        (obs.comentarios && obs.comentarios.trim());
      if (hasText) {
        payload.q16 = {
          positivos: obs.positivos || "",
          mejorar: obs.mejorar || "",
          comentarios: obs.comentarios || "",
        };
      }
    }
    try {
      await submitAttempt(attemptId, payload);

      // Avanza automáticamente al siguiente de la cola
      const next = await getNextAttempt(surveyId);
      if (next) {
        nav(`/encuesta/${next.attempt_id}/step1`, { replace: true });
      } else {
        // Sin siguiente: por ahora a resumen mínimo
        nav("/resumen", { replace: true });
      }
    } catch (e: any) {
      const msg =
        e?.response?.data?.detail ||
        "No se pudo enviar. Verifica conexión o intenta de nuevo.";
      alert(msg);
    }
  }

  return (
    <div className="min-h-screen bg-[#f8f5ef]">
      <USCOHeader subtitle="Encuesta Docente · Paso 2/2" />

      <USCOPage>
        <div className="mb-6">
          <h2 className="text-2xl font-semibold">Paso 2 de 2</h2>
          <p className="text-gray-600">
            Docente actual:{" "}
            <span className="font-medium">{teacherName || "—"}</span>
          </p>
        </div>

        {loading ? (
          <div className="text-gray-500">Cargando…</div>
        ) : (
          <>
            {/* Q10–Q15 */}
            <div className="space-y-5">
              {qsStep2.map((q) => (
                <div
                  key={q.id}
                  className="p-4 bg-gray-50 rounded-xl border border-gray-200"
                >
                  <div className="font-medium mb-2">
                    {q.codigo}. {q.enunciado}
                  </div>
                  <LikertSelect
                    value={(values[q.id] ?? "") as number | ""}
                    onChange={(v) => setValues((s) => ({ ...s, [q.id]: v }))}
                  />
                </div>
              ))}
            </div>

            {/* Q16 opcional */}
            {q16 && (
              <div className="mt-6 p-4 bg-white rounded-xl border border-gray-200">
                <div className="font-semibold mb-3">
                  Q16. Observaciones (opcional)
                </div>
                <div className="grid sm:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium">
                      Aspectos positivos
                    </label>
                    <textarea
                      className="mt-1 w-full border rounded-lg p-3 min-h-[90px] outline-none focus:ring-2 focus:ring-usco-primary/30"
                      value={obs.positivos || ""}
                      onChange={(e) =>
                        setObs((s) => ({ ...s, positivos: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">A mejorar</label>
                    <textarea
                      className="mt-1 w-full border rounded-lg p-3 min-h-[90px] outline-none focus:ring-2 focus:ring-usco-primary/30"
                      value={obs.mejorar || ""}
                      onChange={(e) =>
                        setObs((s) => ({ ...s, mejorar: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Comentarios</label>
                    <textarea
                      className="mt-1 w-full border rounded-lg p-3 min-h-[90px] outline-none focus:ring-2 focus:ring-usco-primary/30"
                      value={obs.comentarios || ""}
                      onChange={(e) =>
                        setObs((s) => ({ ...s, comentarios: e.target.value }))
                      }
                    />
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-between mt-8">
              <Link
                to={`/encuesta/${attemptId}/step1`}
                className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200"
              >
                Regresar
              </Link>
              <button
                onClick={onSubmit}
                disabled={!allAnswered}
                className="px-5 py-2 rounded-xl bg-usco-primary text-white disabled:opacity-60"
              >
                Enviar
              </button>
            </div>
          </>
        )}
      </USCOPage>

      <p className="text-center text-gray-500 mt-8 text-sm">
        © USCO — Prototipo para demostración
      </p>
    </div>
  );
}
