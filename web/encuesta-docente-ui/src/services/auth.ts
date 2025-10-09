import api from "./api";

export async function login(email: string) {
  const { data } = await api.post("/auth/login", { email });
  // servidor devuelve { access_token, token_type } y/o me
  const token = data?.access_token || data?.token || data;
  if (!token) throw new Error("Token no recibido");
  localStorage.setItem("token", token);
  return token;
}

export type MeOut = {
  id: string;
  email: string;
  nombre?: string;
  rol?: string;
};

export async function me(): Promise<MeOut> {
  const { data } = await api.get<MeOut>("/auth/me");
  return data;
}

/** Cierre de sesión robusto + broadcast a otras pestañas. */
export async function logout(opts?: { server?: boolean }) {
  try {
    if (opts?.server) {
      // si no existe el endpoint, no pasa nada
      await api.post("/auth/logout");
    }
  } catch {}
  try {
    // borra estado local
    localStorage.removeItem("token");
    sessionStorage.clear();
    // notifica a otras pestañas
    localStorage.setItem("__logout__", String(Date.now()));
    // limpia la marca para no dejar basura
    localStorage.removeItem("__logout__");
  } catch {}
}
