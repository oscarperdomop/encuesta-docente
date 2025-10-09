import { Link } from "react-router-dom";
export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#f8f5ef] grid place-items-center">
      <div className="bg-white p-8 rounded-2xl shadow-card max-w-md text-center">
        <h1 className="text-2xl font-bold mb-2">404 — No encontrado</h1>
        <p className="text-gray-600 mb-6">La ruta solicitada no existe.</p>
        <Link
          to="/login"
          className="px-5 py-2 rounded-xl bg-usco-primary text-white"
        >
          Ir a Login
        </Link>
      </div>
    </div>
  );
}
