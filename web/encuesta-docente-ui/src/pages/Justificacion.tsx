// src/pages/Justificacion.tsx
import { useNavigate } from "react-router-dom";
import USCOHeader from "@/components/USCOHeader";
import { useAuthStore } from "@/state/authStore";

export default function Justificacion() {
  const nav = useNavigate();
  const user = useAuthStore((state) => state.user);
  const nombre = user?.nombre || user?.email || "Usuario";

  return (
    <div className="min-h-screen bg-[#f8f5ef]">
      <USCOHeader subtitle="Encuesta Docente · Justificación" />

      <main className="max-w-3xl mx-auto px-4 md:px-6 py-8 md:py-12">
        <article className="bg-white rounded-2xl shadow-card p-6 md:p-8">
          <h1 className="text-2xl md:text-3xl font-bold mb-4">
            Justificación de la evaluación
          </h1>

          <p className="text-gray-700 leading-relaxed">
            Estimado/a <span className="font-semibold">{nombre || "—"}</span>,
            esta evaluación tiene como propósito **mejorar continuamente** los
            procesos de enseñanza y aprendizaje del programa. Los resultados se
            utilizarán con fines **académicos y de mejora**, respetando la
            confidencialidad establecida por la institución.
          </p>

          <ul className="list-disc pl-6 text-gray-700 mt-4 space-y-2">
            <li>Fortalecer la calidad docente y los recursos del curso.</li>
            <li>Identificar oportunidades de formación y acompañamiento.</li>
            <li>Retroalimentar a los docentes con indicadores objetivos.</li>
          </ul>

          <p className="text-gray-600 mt-4">
            Al continuar, podrás **seleccionar los docentes** a evaluar. El
            proceso toma pocos minutos y se realiza en **dos pasos** con 16
            preguntas (Q1–Q15 tipo Likert 1–5 y Q16 de observaciones opcional).
          </p>

          <div className="flex justify-end gap-3 mt-8">
            <button
              type="button"
              className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200"
              onClick={() => nav("/intro")}
            >
              Regresar
            </button>
            <button
              className="px-5 py-2 rounded-xl bg-usco-primary text-white"
              onClick={() => nav("/docentes")}
            >
              Continuar
            </button>
          </div>
        </article>

        <p className="text-center text-gray-500 mt-8 text-sm">
          © USCO — Prototipo para demostración
        </p>
      </main>
    </div>
  );
}
