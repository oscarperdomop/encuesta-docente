import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import USCOPage from "@/components/USCOPage";
import { getAttempt, patchAttempt } from "@/services/attempts";
import { getSurveyQuestions, Question } from "@/services/questions";
import LikertSelect from "@/components/LikertSelect";
import { getActiveSurveyId } from "@/store/survey"; // si aún no lo tienes, ver nota al final

type Values = Record<string, number | "">;

export default function Step1() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const nav = useNavigate();

  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [values, setValues] = useState<Values>({});
  const [teacherName, setTeacherName] = useState<string>("");
  const [expired, setExpired] = useState<boolean>(false);

  const surveyId = getActiveSurveyId(); // o lee de contexto/env

  const qsStep1 = useMemo(
    () =>
      questions.filter((q) => q.codigo.match(/^Q([1-9]|0?[1-9])$/)).slice(0, 9),
    [questions]
  );

  const allAnswered = useMemo(
    () =>
      qsStep1.length > 0 &&
      qsStep1.every((q) => values[q.id] !== "" && values[q.id] !== undefined),
    [qsStep1, values]
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
        // Pre-cargar respuestas si existieran
        const init: Values = {};
        for (const a of att.answers || []) {
          if (a.value && a.question_id) init[a.question_id] = a.value;
        }
        // Asegura keys de Q1–Q9 con "" si no hay valor
        qs.filter((q) => q.codigo.match(/^Q([1-9]|0?[1-9])$/))
          .slice(0, 9)
          .forEach((q) => {
            if (init[q.id] === undefined) init[q.id] = "";
          });
        setValues(init);
        setExpired(false);
      } catch {
        setExpired(true);
      } finally {
        setLoading(false);
      }
    })();
  }, [attemptId, surveyId]);

  // Autosave muy básico al cambiar un valor (sin renovar expiración)
  async function setVal(qid: string, v: number | "") {
    const next = { ...values, [qid]: v };
    setValues(next);
    // Guarda solo cuando hay número válido
    if (typeof v === "number" && attemptId) {
      try {
        await patchAttempt(attemptId, { [qid]: v }, false /* no renueva */);
      } catch {
        /* silencioso por ahora */
      }
    }
  }

  function onNext() {
    if (!attemptId) return;
    nav(`/encuesta/${attemptId}/step2`);
  }

  return (
    <div className="min-h-screen bg-[#f8f5ef]">
      <USCOPage subtitle="Encuesta Docente · Paso 1/2">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold">Paso 1 de 2</h2>
          <p className="text-gray-600">
            Docente actual:{" "}
            <span className="font-medium">{teacherName || "—"}</span>
          </p>
        </div>

        {loading ? (
          <div className="text-gray-500">Cargando…</div>
        ) : expired ? (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            La sesión de este intento ha expirado. Regresa a la lista de
            docentes.
          </div>
        ) : (
          <div className="space-y-5">
            {qsStep1.map((q) => (
              <div
                key={q.id}
                className="p-4 bg-gray-50 rounded-xl border border-gray-200"
              >
                <div className="font-medium mb-2">
                  {q.codigo}. {q.enunciado}
                </div>
                <LikertSelect
                  value={(values[q.id] ?? "") as number | ""}
                  onChange={(v) => setVal(q.id, v)}
                />
              </div>
            ))}

            <div className="flex justify-between pt-4">
              <Link
                to="/docentes"
                className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200"
              >
                Regresar a la lista
              </Link>
              <button
                onClick={onNext}
                disabled={!allAnswered}
                className="px-5 py-2 rounded-xl bg-usco-primary text-white disabled:opacity-60"
              >
                Siguiente
              </button>
            </div>
          </div>
        )}
      </USCOPage>

      <p className="text-center text-gray-500 mt-8 text-sm">
        © USCO — Prototipo para demostración
      </p>
    </div>
  );
}
