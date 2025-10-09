// src/pages/Encuesta.tsx
import USCOHeader from "@/components/USCOHeader";

export default function Encuesta() {
  return (
    <div className="min-h-screen bg-usco-bg">
      <USCOHeader subtitle="Encuesta Docente · Paso 1/2" />
      <main className="max-w-3xl mx-auto px-4 md:px-6 py-10">
        <div className="bg-white rounded-2xl shadow-card p-8 text-center">
          <h1 className="text-xl font-semibold mb-2">Encuesta (placeholder)</h1>
          <p className="text-gray-600">
            La siguiente tarea será implementar el Paso 1 con Q1–Q9 y
            validaciones.
          </p>
        </div>
      </main>
    </div>
  );
}
