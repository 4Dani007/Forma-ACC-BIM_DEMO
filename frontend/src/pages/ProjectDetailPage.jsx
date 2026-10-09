import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api, downloadFile } from "../api/client";
import { LevelPill, PageHeader, formatDate, statusClass } from "../components/ui";

export function ProjectDetailPage() {
  const { projectId } = useParams();
  const [query, setQuery] = useState("");
  const [downloadError, setDownloadError] = useState("");
  const project = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api(`/api/projects/${projectId}`),
  });
  const matrix = useQuery({
    queryKey: ["permissions", projectId],
    queryFn: () => api(`/api/projects/${projectId}/permissions`),
  });

  async function save(path, fallback) {
    setDownloadError("");
    try {
      await downloadFile(path, fallback);
    } catch (error) {
      setDownloadError(error.message);
    }
  }

  const detail = project.data;
  const matrixData = matrix.data;
  const folders = (matrixData?.folders || []).filter((folder) => {
    const needle = query.trim().toLocaleLowerCase("es");
    if (!needle) return true;
    return folder.path.toLocaleLowerCase("es").includes(needle);
  });

  if (project.isLoading || matrix.isLoading) return <p className="state">Cargando…</p>;
  if (project.error || matrix.error) {
    return <p className="state state-error">{(project.error || matrix.error).message}</p>;
  }
  if (!detail || !matrixData) return null;

  return (
    <>
      <PageHeader
              eyebrow={detail.code}
              title={detail.name}
              lede={`${detail.client} · ${detail.location} · Fase ${detail.phase}`}
              actions={
                <>
                  <button type="button" className="button button-ghost" onClick={() => save(`/api/projects/${projectId}/metadata`, "metadatos.json")}>
                    Metadatos
                  </button>
                  <button type="button" className="button button-ghost" onClick={() => save(`/api/projects/${projectId}/permissions/export?format=csv`, "permisos.csv")}>
                    CSV
                  </button>
                  <button type="button" className="button" onClick={() => save(`/api/projects/${projectId}/permissions/export?format=xlsx`, "permisos.xlsx")}>
                    Excel
                  </button>
                </>
              }
            />
            <p className="meta-row">
              <span className={statusClass(detail.status)}>{detail.status}</span>
              <span>Alta {formatDate(detail.created_at)}</span>
              <Link to={`/permisos?proyecto=${detail.id}`}>Cambiar permisos</Link>
              <Link to={`/comparador?a=${detail.id}`}>Comparar</Link>
            </p>
            {downloadError ? <p className="state state-error">{downloadError}</p> : null}

            <section className="panel">
              <div className="panel-head">
                <h2>Permisos por carpeta y rol</h2>
                <label className="search">
                  <span className="sr-only">Buscar carpeta</span>
                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Buscar carpeta"
                  />
                </label>
              </div>
              <div className="table-wrap">
                <table>
                  <caption className="sr-only">Matriz de permisos</caption>
                  <thead>
                    <tr>
                      <th>Carpeta</th>
                      {matrixData.roles.map((role) => (
                        <th key={role.id}>{role.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {folders.map((folder) => (
                      <tr key={folder.id} className={folder.depth === 0 ? "row-root" : undefined}>
                        <td>
                          <span className="folder-label" style={{ paddingLeft: folder.depth * 18 }} title={folder.path}>
                            {folder.name}
                          </span>
                        </td>
                        {matrixData.roles.map((role) => (
                          <td key={role.id}>
                            <LevelPill level={folder.permissions[role.id]} />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {folders.length === 0 ? <p className="state">Ninguna carpeta coincide con la búsqueda.</p> : null}
            </section>

            <section className="panel">
              <div className="panel-head">
                <h2>Miembros</h2>
                <Link to="/asignacion">Asignar desde CSV</Link>
              </div>
              <div className="table-wrap">
                <table>
                  <caption className="sr-only">Personas asignadas al proyecto</caption>
                  <thead>
                    <tr>
                      <th>Nombre</th>
                      <th>Correo</th>
                      <th>Empresa</th>
                      <th>Rol</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...detail.members]
                      .sort((a, b) => a.name.localeCompare(b.name, "es"))
                      .map((member) => (
                        <tr key={member.user_id}>
                          <td>{member.name}</td>
                          <td className="mono">{member.email}</td>
                          <td>{member.company}</td>
                          <td>{member.role}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </section>
    </>
  );
}
