import { ReactNode } from "react";

export default function ConfirmModal({
  open,
  title = "Confirmar",
  children,
  onClose,
  onConfirm,
  confirmText = "Sí, enviar",
  cancelText = "Cancelar",
  loading = false,
}: {
  open: boolean;
  title?: string;
  children?: ReactNode;
  onClose: () => void;
  onConfirm: () => void;
  confirmText?: string;
  cancelText?: string;
  loading?: boolean;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-card">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
        <div className="p-6 text-gray-700">{children}</div>
        <div className="p-6 pt-0 flex justify-end gap-3">
          <button
            className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200"
            onClick={onClose}
            disabled={loading}
          >
            {cancelText}
          </button>
          <button
            className="px-4 py-2 rounded-xl bg-usco-primary text-white disabled:opacity-60"
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? "Enviando..." : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
