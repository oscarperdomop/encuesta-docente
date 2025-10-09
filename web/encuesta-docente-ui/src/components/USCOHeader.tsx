import { Link } from "react-router-dom";

export default function USCOHeader({
  subtitle = "Encuesta Docente · Presentación",
}: {
  subtitle?: string;
}) {
  return (
    <header className="bg-transparent">
      <link
        rel="shortcut icon"
        href="https://www.usco.edu.co/imagen-institucional/favicon.ico"
        type="image/x-icon"
      />

      <div className="max-w-5xl mx-auto px-4 md:px-6 py-4 flex items-center gap-3">
        <Link
          to="/"
          className="w-10 h-10 rounded-full bg-usco-primary text-white grid place-items-center font-bold"
        >
          US
        </Link>
        <div className="min-w-0">
          <div className="font-semibold text-base sm:text-lg truncate">
            Universidad Surcolombiana
          </div>
          <div className="text-gray-500 text-sm truncate">{subtitle}</div>
        </div>
      </div>
    </header>
  );
}
