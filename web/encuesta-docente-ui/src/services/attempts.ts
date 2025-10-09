import api from "@/services/api";

/* ---------- Tipos ---------- */
export type LikertAnswer = { question_id: string; value: number };

export type AttemptOut = {
  id: string;
  survey_id: string;
  teacher_id: string;
  estado: "en_progreso" | "enviado" | "expirado" | "fallido";
  intento_nro: number;
  expires_at: string | null;
};

export type NextItemOut = {
  survey_id: string;
  teacher_id: string;
  teacher_nombre: string;
  attempt_id: string;
  expires_at: string | null;
  intento_nro: number;
};

export type Q16Text = {
  positivos?: string;
  mejorar?: string;
  comentarios?: string;
};

/* ---------- Helpers de progreso local opcionales ---------- */
const key = (attemptId: string, step: "step1" | "step2") =>
  `attempt:${attemptId}:${step}`;

export function saveStep1(attemptId: string, answers: LikertAnswer[]) {
  sessionStorage.setItem(key(attemptId, "step1"), JSON.stringify(answers));
}
export function loadStep1(attemptId: string): LikertAnswer[] {
  try {
    return JSON.parse(sessionStorage.getItem(key(attemptId, "step1")) || "[]");
  } catch {
    return [];
  }
}
export function clearAttemptLocal(attemptId: string) {
  sessionStorage.removeItem(key(attemptId, "step1"));
  sessionStorage.removeItem(key(attemptId, "step2"));
}

/* ---------- API calls ---------- */

export async function createAttempts(surveyId: string, teacherIds: string[]) {
  const { data } = await api.post<AttemptOut[]>("/attempts", {
    survey_id: surveyId,
    teacher_ids: teacherIds,
  });
  return data;
}

export async function getNextAttempt(surveyId: string) {
  // 200 => objeto; 204 => sin contenido
  const res = await api.get<NextItemOut | null>("/attempts/next", {
    validateStatus: () => true,
    params: { survey_id: surveyId },
  });
  return res.status === 200 ? (res.data as NextItemOut) : null;
}

export type AttemptDetails = {
  id: string;
  survey_id: string;
  teacher_id: string;
  estado: string;
  expires_at: string | null;
  answers: { question_id: string; value?: number; texto?: any }[];
};

export async function getAttempt(attemptId: string) {
  const { data } = await api.get(`/attempts/${attemptId}`);
  return data;
}

/** Guardado incremental del progreso (autosave ligero). */
export async function saveProgress(
  attemptId: string,
  payload: {
    likert?: Array<{ question_id: string; value: number }>;
    observaciones?: Q16Text;
  }
) {
  const { data } = await api.patch(`/attempts/${attemptId}`, payload);
  return data;
}

export type SubmitOut = {
  estado: "enviado";
  scores: {
    total: number | null;
    secciones: { section_id: string; titulo: string; score: number }[];
  };
};

/** Envío final: 15 respuestas (value) + Q16 opcional. */
export async function submitAttempt(
  attemptId: string,
  answers: LikertAnswer[],
  textos?: Q16Text
) {
  // Sanitiza textos
  const clean = {
    positivos: textos?.positivos?.trim() || undefined,
    mejorar: textos?.mejorar?.trim() || undefined,
    comentarios: textos?.comentarios?.trim() || undefined,
  };
  const hasQ16 = !!clean.positivos || !!clean.mejorar || !!clean.comentarios;

  // ¡OJO!: el backend espera `answers[*].value`
  const body: any = {
    answers: answers.map((a) => ({
      question_id: a.question_id,
      value: a.value,
    })),
  };

  // Clave canónica (la que te funcionó): `textos`
  if (hasQ16) {
    body.textos = clean;

    // Compatibilidad amplia (por si el backend mira otra clave)
    body.q16 = clean;
    body.observaciones = clean;
    body.texto = clean;
  }

  const { data } = await api.post<SubmitOut>(
    `/attempts/${attemptId}/submit`,
    body
  );
  return data;
}

/* ---------- Resumen de turno ---------- */
export type AttemptsSummaryItem = {
  teacher_id: string;
  teacher_nombre: string;
  estado: "en_progreso" | "enviado" | "pendiente" | string;
};

export type AttemptsSummary = {
  enviados: number;
  en_progreso: number;
  pendientes: number;
  items: AttemptsSummaryItem[];
  can_finish: boolean;
};

export async function getAttemptsSummary(
  surveyId: string
): Promise<AttemptsSummary> {
  const { data } = await api.get<any>("/attempts/summary", {
    params: { survey_id: surveyId },
  });

  const counts =
    data?.counts ||
    data?.totales ||
    data?.totals ||
    data?.resumen ||
    data ||
    {};

  const pickNum = (obj: any, keys: string[], def = 0) => {
    for (const k of keys) {
      const v = obj?.[k];
      if (typeof v === "number" && !Number.isNaN(v)) return v;
    }
    return def;
  };

  const enviados = pickNum(counts, [
    "enviados",
    "sent",
    "enviadas",
    "total_enviados",
  ]);
  const en_progreso = pickNum(counts, [
    "en_progreso",
    "in_progress",
    "progreso",
    "total_en_progreso",
  ]);
  const pendientes = pickNum(counts, [
    "pendientes",
    "pending",
    "total_pendientes",
  ]);

  const items: AttemptsSummaryItem[] = Array.isArray(data?.items)
    ? data.items
    : Array.isArray(data?.docentes)
    ? data.docentes
    : [];

  const can_finish =
    typeof data?.can_finish === "boolean"
      ? data.can_finish
      : pendientes === 0 && en_progreso === 0;

  return { enviados, en_progreso, pendientes, items, can_finish };
}
