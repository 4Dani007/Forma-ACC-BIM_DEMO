import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { LevelPill, PageHeader, PageState } from "../components/ui";

const STATUS_LABEL = {
  permission_mismatch: "Permiso distinto",
  role_missing: "Rol sin permiso",
  missing_in_a: "Carpeta faltante",
  missing_in_b: "Carpeta faltante",
  same: "Igual",
};

export function ComparePage() {
  const [params] = useSearchParams();
  const projects = useQuery({ queryKey: ["projects"], queryFn: () => api("/api/projects") });
  const [left, setLeft] = useState(params.get("a") || "");
  const [right, setRight] = useState(params.get("b") || "");
  const [onlyDiffs, setOnlyDiffs] = useState(true);
  const [defaultsReady, setDefaultsReady] = useState(false);

  useEffect(() => {
    if (!projects.data || defaultsReady) return;
    const ids = new Set(projects.data.map((project) => project.id));
    if (!params.get("a") && ids.has("torre-1")) setLeft("torre-1");
    if (!params.get("b") && ids.has("torre-2")) setRight("torre-2");
    setDefaultsReady(true);
  }, [projects.data, defaultsReady, params]);

  const compare = useQuery({
    queryKey: ["compare", left, right],
    queryFn: () => api(`/api/compare?a=${encodeURIComponent(left)}&b=${encodeURIComponent(right)}`),
    enabled: Boolean(left && right),
  });

  const result = compare.data;
  const rows = (result?.rows || []).filter((row) => (onlyDiffs ? row.status !== "same" : true));

  function labelFor(status) {
    if (!result) return STATUS_LABEL[status] || status;
    if (status === "missing_in_a") return `Falta en ${result.project_a.name}`;
    if (status === "missing_in_b") return `Falta en ${result.project_b.name}`;
    return STATUS_LABEL[status] || status;
  }

  return (
    <>
      <PageHeader
        eyebrow="Estructura"
        title="Comparador"
        lede="Las carpetas se emparejan por ruta, no por identificador. Así dos obras distintas se pueden contrastar."
      />
      <PageState isLoading={projects.isLoading} error={projects.error}>
        <section className="panel filters">
          <label>
            Proyecto A
            <select value={left} onChange={(event) => setLeft(event.target.value)}>
              <option value="">Selecciona</option>
              {(projects.data || []).map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Proyecto B
            <select value={right} onChange={(event) => setRight(event.target.value)}>
              <option value="">Selecciona</option>
              {(projects.data || []).map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="check-inline">
            <input type="checkbox" checked={onlyDiffs} onChange={(event) => setOnlyDiffs(event.target.checked)} />
            Solo diferencias
          </label>
        </section>

        <ul className="legend">
          <li>
            <i className="swatch swatch-mismatch" /> Permiso distinto
          </li>
          <li>
            <i className="swatch swatch-role" /> Rol sin permiso
          </li>
          <li>
            <i className="swatch swatch-missing" /> Carpeta faltante
          </li>
        </ul>

        <PageState isLoading={compare.isLoading} error={compare.error}>
          {result ? (
            <section className="panel">
              <div className="summary-row">
                <span>Carpetas {result.summary.total}</span>
                <span>Iguales {result.summary.same}</span>
                <span>Permiso distinto {result.summary.permission_mismatch}</span>
                <span>Rol sin permiso {result.summary.role_missing}</span>
                <span>
                  Faltan {result.summary.missing_in_a + result.summary.missing_in_b}
                </span>
              </div>
              <p className="confirm-note">
                Mostrando {rows.length} de {result.summary.total}. A la izquierda, {result.project_a.name}. A la
                derecha, {result.project_b.name}.
              </p>
              <div className="table-wrap">
                <table>
                  <caption className="sr-only">Diferencias de permisos entre los dos proyectos</caption>
                  <thead>
                    <tr>
                      <th>Ruta</th>
                      <th>Diferencia</th>
                      <th>{result.project_a.code}</th>
                      <th>{result.project_b.code}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.path} className={`diff diff-${row.status}`}>
                        <td className="mono">{row.path}</td>
                        <td>{labelFor(row.status)}</td>
                        <td>
                          <Side permissions={row.permissions_a} diffs={row.diffs} side="a" missing={row.status === "missing_in_a"} />
                        </td>
                        <td>
                          <Side permissions={row.permissions_b} diffs={row.diffs} side="b" missing={row.status === "missing_in_b"} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {rows.length === 0 ? <p className="state">No hay diferencias entre estos proyectos.</p> : null}
            </section>
          ) : null}
        </PageState>
      </PageState>
    </>
  );
}

function Side({ permissions, diffs, side, missing }) {
  if (missing) return <span className="muted">Esta carpeta no existe</span>;
  const changed = (diffs || []).filter((diff) => (side === "a" ? diff.level_a : diff.level_b) !== undefined);
  const roles = changed.length ? changed.map((diff) => diff.role) : Object.keys(permissions);
  if (!roles.length) return <span className="muted">Sin permisos</span>;
  return (
    <ul className="diff-list">
      {roles.map((role) => (
        <li key={role}>
          <span>{role}</span>
          <LevelPill level={permissions[role]} />
        </li>
      ))}
    </ul>
  );
}
