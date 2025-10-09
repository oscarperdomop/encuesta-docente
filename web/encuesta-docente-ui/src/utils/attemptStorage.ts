// guarda / lee respuestas parciales por intento usando sessionStorage
export type LikertAnswer = { question_id: string; valor: number };

const k = (attemptId: string, step: "step1" | "step2") =>
  `attempt:${attemptId}:${step}`;

export function saveStep1(attemptId: string, answers: LikertAnswer[]) {
  sessionStorage.setItem(k(attemptId, "step1"), JSON.stringify(answers));
}

export function loadStep1(attemptId: string): LikertAnswer[] {
  try {
    return JSON.parse(sessionStorage.getItem(k(attemptId, "step1")) || "[]");
  } catch {
    return [];
  }
}

export function clearAttemptLocal(attemptId: string) {
  sessionStorage.removeItem(k(attemptId, "step1"));
  sessionStorage.removeItem(k(attemptId, "step2"));
}
