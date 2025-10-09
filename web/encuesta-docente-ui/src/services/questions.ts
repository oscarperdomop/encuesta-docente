// src/services/questions.ts
import api from "./api";

export type Question = {
  id: string;
  survey_id: string;
  section: string; // título de sección
  codigo: string; // Q1..Q16
  enunciado: string;
  orden: number;
  tipo: "likert" | "texto";
  peso: number | null;
};

export async function getSurveyQuestions(surveyId: string) {
  const { data } = await api.get<Question[]>(`/surveys/${surveyId}/questions`);
  // Orden defensivo por "orden" (el API ya ordena, pero lo dejamos claro)
  return [...data].sort((a, b) => a.orden - b.orden);
}
