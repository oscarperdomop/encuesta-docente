import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, me } from "@/services/auth";

export default function Login() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nav = useNavigate();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email.trim().toLowerCase());
      await me(); // verifica token
      nav("/intro", { replace: true });
    } catch (err) {
      if (
        err &&
        typeof err === "object" &&
        "response" in err &&
        err.response &&
        "data" in err.response &&
        err.response.data &&
        "detail" in err.response.data
      ) {
        setError(
          (err as { response: { data: { detail: string } } }).response.data
            .detail
        );
      } else {
        setError("Correo no autorizado");
      }
      localStorage.removeItem("token");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#f8f5ef]">
      <link
        rel="shortcut icon"
        href="https://www.usco.edu.co/imagen-institucional/favicon.ico"
        type="image/x-icon"
      />
      <div className="max-w-xl mx-auto pt-10 px-4">
        {/* Encabezado */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-full bg-usco-primary text-white grid place-items-center font-bold">
            US
          </div>
          <div>
            <div className="font-semibold text-lg">
              Universidad Surcolombiana
            </div>
            <div className="text-gray-500">Encuesta Docente · Login</div>
          </div>
        </div>

        {/* Formulario */}
        <form
          onSubmit={onSubmit}
          className="bg-white p-8 rounded-2xl shadow-card"
        >
          <h1 className="text-2xl font-bold mb-2">Iniciar sesión</h1>
          <p className="text-gray-600 mb-6">
            Acceso con correo institucional <b>@usco.edu.co</b>
          </p>

          <label className="text-sm font-medium" htmlFor="email">
            Correo institucional
          </label>
          <input
            id="email"
            type="email"
            className="mt-1 w-full border rounded-xl p-3 outline-none focus:ring-2 focus:ring-usco-primary/30 focus:border-usco-primary"
            placeholder="usuario@usco.edu.co"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          {error && <div className="text-red-600 mt-2">{error}</div>}

          <div className="flex gap-3 justify-end mt-6">
            <button
              type="button"
              className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200"
              onClick={() => setEmail("")}
            >
              Cancelar
            </button>
            <button
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-usco-primary text-white disabled:opacity-60"
            >
              {loading ? "Entrando..." : "Entrar"}
            </button>
          </div>
        </form>

        <p className="text-center text-gray-500 mt-8 text-sm">
          © USCO — Prototipo para demostración
        </p>
      </div>
    </div>
  );
}
