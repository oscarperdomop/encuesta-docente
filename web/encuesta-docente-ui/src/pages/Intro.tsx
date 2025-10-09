import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { me } from "@/services/auth";
import USCOHeader from "@/components/USCOHeader";

export default function Intro() {
  const [nombre, setNombre] = useState<string>("");
  const nav = useNavigate();

  useEffect(() => {
    me()
      .then((u) => setNombre(u?.nombre || u?.email || "Usuario"))
      .catch(() => {
        localStorage.removeItem("token");
        nav("/login", { replace: true });
      });
  }, [nav]);

  return (
    <div className="min-h-screen bg-[#f8f5ef] flex flex-col">
      {/* Header institucional reutilizable */}
      <USCOHeader subtitle="Encuesta Docente · Presentación" />

      {/* Resto de la página centrado vertical/horizontal */}
      <main className="flex-1 grid place-items-center px-4">
        <div className="w-full max-w-xl">
          <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-card">
            <h1 className="text-2xl font-bold mb-3">
              Bienvenido/a {nombre || "—"}.
            </h1>

            <p className="text-gray-700 leading-relaxed">
              Facultad de Educación — Programa Lic. en Matemáticas.
              <br />
              <span className="font-semibold">
                Evaluación Docente (periodo vigente)
              </span>
              .
            </p>

            <p className="text-gray-600 mt-4">
              A continuación encontrarás la justificación y el propósito de la
              evaluación. Presiona <b>Continuar</b> para avanzar.
            </p>

            <div className="flex justify-end gap-3 mt-8">
              <button
                type="button"
                className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200"
                onClick={() => nav("/login")}
              >
                Cambiar de usuario
              </button>
              <button
                className="px-5 py-2 rounded-xl bg-usco-primary text-white"
                onClick={() => nav("/justificacion")}
              >
                Continuar
              </button>
            </div>
          </div>

          <p className="text-center text-gray-500 mt-8 text-sm">
            © USCO — Prototipo para demostración
          </p>
        </div>
      </main>
    </div>
  );
}
