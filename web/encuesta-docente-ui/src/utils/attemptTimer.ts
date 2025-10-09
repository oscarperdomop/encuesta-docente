// Claves para persistir expiry por attempt (ms epoch)
const EXP_KEY = (id: string) => `attempt:${id}:expiresAt`;

export function saveAttemptExpiry(
  attemptId: string,
  expiresISO: string | null
) {
  try {
    if (!attemptId) return;
    if (expiresISO) {
      const ts = new Date(expiresISO).getTime();
      if (Number.isFinite(ts))
        localStorage.setItem(EXP_KEY(attemptId), String(ts));
    } else {
      localStorage.removeItem(EXP_KEY(attemptId));
    }
  } catch {}
}

export function loadAttemptExpiry(attemptId: string): number | null {
  try {
    const raw = localStorage.getItem(EXP_KEY(attemptId));
    if (!raw) return null;
    const n = Number(raw);
    return Number.isFinite(n) ? n : null;
  } catch {
    return null;
  }
}

export function clearAttemptExpiry(attemptId: string) {
  try {
    localStorage.removeItem(EXP_KEY(attemptId));
  } catch {}
}
