// src/services/catalogs.ts
import api from "@/services/api";

export type SurveyActiva = {
  id: string;
  codigo: string;
  nombre: string;
  estado: "activa" | "inactiva";
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
};

export type TeacherRow = {
  id: string;
  identificador: string;
  nombre: string;
  programa?: string | null;
  estado: "activo" | "inactivo";
};

export type QuestionRow = {
  id: string;
  codigo: string;
  enunciado: string;
  orden: number;
  tipo: "likert" | "texto";
  peso: number;
  section: string; // viene del JOIN en tu API
};

export async function getActiveSurveys() {
  const { data } = await api.get("/surveys/activas");
  return data;
}

// Trae todas las preguntas de la encuesta
export async function getSurveyQuestions(surveyId: string) {
  const { data } = await api.get<QuestionRow[]>(
    `/surveys/${surveyId}/questions`
  );
  return data;
}

export async function getSurveyTeachers(
  surveyId: string,
  q?: string,
  limit = 50,
  offset = 0
) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  params.set("limit", String(limit));
  params.set("offset", String(offset));

  const { data } = await api.get<TeacherRow[]>(
    `/surveys/${surveyId}/teachers${params.toString() ? `?${params}` : ""}`
  );
  return data;
}

export async function getQuestions(surveyId: string) {
  const { data } = await api.get<QuestionRow[]>(
    `/surveys/${surveyId}/questions`
  );
  return data;
}
