import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { PageHeader, PageState, Tag } from "../components/ui";
import { parseCsv } from "../utils/csv";

export function BulkAssignPage() {
  const queryClient = useQueryClient();
  const projects = useQuery({ queryKey: ["projects"], queryFn: () => api("/api/projects") });
  const [rows, setRows] = useState(null);
  const [fileName, setFileName] = useState("");
  const [parseError, setParseError] = useState("");

  const preview = useMutation({
    mutationFn: (payload) =>
      api("/api/memberships/bulk/preview", {
        method: "POST",
        body: JSON.stringify({ rows: payload }),
      }),
  });
  const apply = useMutation({
    mutationFn: (payload) =>
      api("/api/memberships/bulk/apply", {
        method: "POST",
        body: JSON.stringify({ rows: payload }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });

  function loadFile(file) {
    if (!file) return;
    setFileName(file.name);
    setParseError("");
    apply.reset();
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = parseCsv(String(reader.result || ""));
        setRows(parsed);
        preview.mutate(parsed);
      } catch (error) {
        setRows(null);
        preview.reset();
        setParseError(error.message);
      }
    };
    reader.readAsText(file);
  }

  const plan = apply.data || preview.data;
  const ready = (plan?.summary.applicable || 0) + (plan?.summary.update_role || 0);

  return (
    <>
      <PageHeader
        eyebrow="Usuarios"
        title="Asignación masiva"
        lede="Carga un CSV, revisa qué pasará con cada fila y confirma. La vista previa no escribe nada."
      />
      <PageState isLoading={projects.isLoading} error={projects.error}>
        <section className="panel">
          <div className="panel-head">
            <h2>Archivo</h2>
            <a href="/usuarios_ejemplo.csv" download>
              Descargar CSV de ejemplo
            </a>
          </div>
          <label
            className="dropzone"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              loadFile(event.dataTransfer.files?.[0]);
            }}
          >
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => loadFile(event.target.files?.[0])}
            />
            <strong>{fileName || "Suelta el CSV o elige un archivo"}</strong>
            <span>Columnas: nombre, correo, empresa, rol, proyectos. Varios proyectos se separan con punto y coma.</span>
          </label>
          <ul className="code-list">
            {(projects.data || []).map((project) => (
              <li key={project.id}>
                <span className="mono">{project.code}</span>
                {project.name}
              </li>
            ))}
          </ul>
          {parseError ? <p className="state state-error">{parseError}</p> : null}
        </section>

        {preview.isPending ? <p className="state">Preparando la vista previa…</p> : null}
        {preview.isError ? <p className="state state-error">{preview.error.message}</p> : null}

        {plan ? (
          <section className="panel">
            <div className="panel-head">
              <h2>{apply.data ? "Resultado" : "Vista previa"}</h2>
              <button
                type="button"
                className="button"
                disabled={!rows || ready === 0 || apply.isPending || Boolean(apply.data)}
                onClick={() => apply.mutate(rows)}
              >
                {apply.isPending ? "Aplicando…" : `Confirmar ${ready} cambios`}
              </button>
            </div>
            <div className="summary-row">
              <span>Filas {plan.summary.total}</span>
              <span>Nuevas {plan.summary.applicable}</span>
              <span>Cambios de rol {plan.summary.update_role}</span>
              <span>Ya eran miembros {plan.summary.already_member}</span>
              <span>Rechazadas {plan.summary.rejected}</span>
              {apply.data ? <span>Aplicadas {apply.data.summary.applied}</span> : null}
            </div>
            {apply.isError ? <p className="state state-error">{apply.error.message}</p> : null}
            {apply.data ? (
              <p className="confirm-note">
                Los cambios quedaron registrados. <Link to="/registro">Ver el registro</Link>
              </p>
            ) : null}
            <div className="table-wrap">
              <table>
                <caption className="sr-only">Resultado de cada fila del CSV</caption>
                <thead>
                  <tr>
                    <th>Fila</th>
                    <th>Persona</th>
                    <th>Proyecto</th>
                    <th>Rol</th>
                    <th>Estado</th>
                    <th>Detalle</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.rows.map((row, index) => (
                    <tr key={`${row.line}-${row.project}-${index}`}>
                      <td>{row.line}</td>
                      <td>
                        {row.name}
                        <span className="sub">{row.email}</span>
                      </td>
                      <td>{row.project || "—"}</td>
                      <td>{row.role || "—"}</td>
                      <td>
                        <Tag kind={row.status} />
                      </td>
                      <td>{row.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
      </PageState>
    </>
  );
}
