// src/store/survey.ts
export function getActiveSurveyId() {
  // por ahora, guarda el survey_id elegido en localStorage cuando el usuario entra desde Intro/Justificación
  return localStorage.getItem("survey_id") || "";
}
