// src/router.tsx
import { createBrowserRouter, Navigate } from "react-router-dom";

import Login from "@/pages/Login";
import Intro from "@/pages/Intro";
import Justificacion from "@/pages/Justificacion";
import DocentesSelect from "@/pages/DocentesSelect";
import SurveyStep1 from "@/pages/SurveyStep1";
import SurveyStep2 from "@/pages/SurveyStep2";
import ProtectedRoute from "@/routes/ProtectedRoute";
import NotFound from "@/pages/NotFound";
import ResumenTurno from "@/pages/ResumenTurno";

export const router = createBrowserRouter(
  [
    {
      path: "/",
      errorElement: <NotFound />,
      children: [
        // Inicio: si no hay nada, manda a login.
        { index: true, element: <Navigate to="/login" replace /> },

        // Público
        { path: "login", element: <Login /> },

        // Privado
        {
          path: "intro",
          element: (
            <ProtectedRoute>
              <Intro />
            </ProtectedRoute>
          ),
        },
        {
          path: "justificacion",
          element: (
            <ProtectedRoute>
              <Justificacion />
            </ProtectedRoute>
          ),
        },
        {
          path: "docentes",
          element: (
            <ProtectedRoute>
              <DocentesSelect />
            </ProtectedRoute>
          ),
        },

        // Encuesta — SIEMPRE con attemptId
        {
          path: "encuesta/:attemptId/step1",
          element: (
            <ProtectedRoute>
              <SurveyStep1 />
            </ProtectedRoute>
          ),
        },
        {
          path: "encuesta/:attemptId/step2",
          element: (
            <ProtectedRoute>
              <SurveyStep2 />
            </ProtectedRoute>
          ),
        },
        {
          path: "resumen",
          element: (
            <ProtectedRoute>
              <ResumenTurno />
            </ProtectedRoute>
          ),
        },
        // Si alguien entra a /encuesta/:attemptId sin step ⇒ redirige a step1
        {
          path: "encuesta/:attemptId",
          element: <Navigate to="step1" replace />,
        },

        // 404 explícito
        { path: "*", element: <NotFound /> },
      ],
    },
  ],
  {
    future: {
      v7_startTransition: true,
      v7_relativeSplatPath: true,
    },
  }
);
