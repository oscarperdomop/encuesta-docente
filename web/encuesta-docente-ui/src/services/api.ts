import axios from "axios";

const BASE =
  (import.meta.env.VITE_API_URL as string) || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: BASE,
  timeout: Number(import.meta.env.VITE_API_TIMEOUT || 10000),
});

api.interceptors.request.use((config) => {
  const t = localStorage.getItem("token");
  if (t) (config.headers ??= {}).Authorization = `Bearer ${t}`;
  return config;
});

// (Opcional recomendado) Si el token vence, lo limpiamos.
api.interceptors.response.use(
  (r) => r,
  (err) => {
    const status = err?.response?.status;
    if (status === 401 || status === 419 || status === 440) {
      try {
        localStorage.removeItem("token");
        sessionStorage.clear();
      } finally {
        if (location.pathname !== "/login") location.replace("/login");
      }
    }
    return Promise.reject(err);
  }
);

console.info("[API] baseURL =", api.defaults.baseURL); // diagnóstico
export default api;
