import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";

const LINKS = [
  { to: "/", label: "Proyectos", end: true },
  { to: "/asignacion", label: "Asignación" },
  { to: "/permisos", label: "Permisos" },
  { to: "/comparador", label: "Comparador" },
  { to: "/registro", label: "Registro" },
];

export function Layout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [notice, setNotice] = useState("");
  const health = useQuery({
    queryKey: ["health"],
    queryFn: () => api("/api/health"),
    retry: 1,
  });
  const reset = useMutation({
    mutationFn: () => api("/api/demo/reset", { method: "POST" }),
    onSuccess: async () => {
      await queryClient.invalidateQueries();
      setNotice("Datos de ejemplo restaurados.");
      navigate("/");
    },
  });

  function onReset() {
    const confirmed = window.confirm(
      "Esto borra los cambios hechos en la demostración y vuelve a cargar los datos de ejemplo.",
    );
    if (!confirmed) return;
    setNotice("");
    reset.mutate();
  }

  return (
    <div className="shell">
      <a className="skip" href="#contenido">
        Saltar al contenido
      </a>
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            S
          </span>
          <div>
            <strong>Senda</strong>
            <small>Permisos de obra</small>
          </div>
        </div>
        <nav aria-label="Secciones">
          {LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end}>
              {link.label}
            </NavLink>
          ))}
        </nav>
        <p className="aside-note">Datos ficticios. Esta demo no se conecta a ningún servicio externo.</p>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <p className="notice" role="status">
            {reset.isError ? reset.error.message : notice}
          </p>
          <button type="button" className="button button-ghost" onClick={onReset} disabled={reset.isPending}>
            {reset.isPending ? "Restaurando…" : "Restaurar datos de ejemplo"}
          </button>
        </header>
        {health.isError ? (
          <p className="banner" role="alert">
            No hay conexión con la API. En local debe estar disponible en el puerto 8000.
          </p>
        ) : null}
        <main id="contenido">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
