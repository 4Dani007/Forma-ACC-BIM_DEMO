const BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

export function apiUrl(path) {
  return `${BASE}${path}`;
}

export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response;
  try {
    response = await fetch(apiUrl(path), { ...options, headers });
  } catch {
    throw new Error("No hay conexión con la API. Revisa que el backend esté en marcha.");
  }

  if (!response.ok) {
    let detail = "No se pudo completar la operación";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* la respuesta de error no trae JSON */
    }
    throw new Error(detail);
  }

  if (response.status === 204) return null;
  const type = response.headers.get("content-type") || "";
  if (type.includes("application/json")) return response.json();
  return response.blob();
}

export async function downloadFile(path, fallbackName) {
  let response;
  try {
    response = await fetch(apiUrl(path));
  } catch {
    throw new Error("No hay conexión con la API. Revisa que el backend esté en marcha.");
  }
  if (!response.ok) {
    throw new Error("No se pudo descargar el archivo");
  }
  const blob = await response.blob();
  const header = response.headers.get("content-disposition") || "";
  const match = /filename="([^"]+)"/.exec(header);
  const filename = match?.[1] || fallbackName;
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
