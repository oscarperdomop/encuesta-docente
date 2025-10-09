import React from "react";
import USCOHeader from "./USCOHeader";

type MaxW = "xl" | "2xl" | "3xl" | "4xl" | "5xl";

const MAXW_CLASS: Record<MaxW, string> = {
  xl: "max-w-xl",
  "2xl": "max-w-2xl",
  "3xl": "max-w-3xl",
  "4xl": "max-w-4xl",
  "5xl": "max-w-5xl",
};

type Props = {
  /** Subtítulo bajo el logo en el header */
  subtitle?: string;
  /** Anchura máxima del contenedor central */
  maxW?: MaxW;
  /** Clases extra para el <main> */
  className?: string;
  /** Mostrar pie de página sencillo */
  showFooter?: boolean;
  children: React.ReactNode;
};

export default function USCOPage({
  subtitle = "Encuesta Docente",
  maxW = "5xl",
  className = "",
  showFooter = true,
  children,
}: Props) {
  const maxw = MAXW_CLASS[maxW] ?? MAXW_CLASS["5xl"];

  return (
    <div className="min-h-screen bg-[#f8f5ef]">
      <USCOHeader subtitle={subtitle} />

      <main className={`mx-auto px-4 md:px-6 py-6 ${maxw} ${className}`}>
        {children}
      </main>

      {showFooter && (
        <p className="text-center text-gray-500 mt-8 mb-6 text-sm">
          © USCO — Prototipo para demostración
        </p>
      )}
    </div>
  );
}
