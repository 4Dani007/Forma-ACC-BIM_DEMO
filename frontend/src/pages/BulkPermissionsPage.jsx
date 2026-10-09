import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { LevelPill, PageHeader, PageState, Tag } from "../components/ui";

const LEVELS = [
  ["ver", "Ver"],
  ["descargar", "Descargar"],
  ["editar", "Editar"],
  ["administrar", "Administrar"],
];

function withDescendants(folders, folderId) {
  const children = folders.filter((folder) => folder.parent_id === folderId).map((folder) => folder.id);
  return [folderId, ...children.flatMap((id) => withDescendants(folders, id))];
}

export function BulkPermissionsPage() {
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const projectId = params.get("proyecto") || "";
  const [selected, setSelected] = useState(() => new Set());
  const [roleId, setRoleId] = useState("");
  const [level, setLevel] = useState("editar");

  const projects = useQuery({ queryKey: ["projects"], queryFn: () => api("/api/projects") });
  const matrix = useQuery({
    queryKey: ["permissions", projectId],
    queryFn: () => api(`/api/projects/${projectId}/permissions`),
    enabled: Boolean(projectId),
  });

  const payload = useMemo(
    () => ({
      project_id: projectId,
      folder_ids: [...selected],
      role_id: roleId,
      level,
    }),
    [projectId, selected, roleId, level],
  );

  const preview = useMutation({
    mutationFn: (body) =>
      api("/api/permissions/bulk/preview", { method: "POST", body: JSON.stringify(body) }),
  });
  const apply = useMutation({
    mutationFn: (body) =>
      api("/api/permissions/bulk/apply", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["permissions", projectId] });
      queryClient.invalidateQueries({ queryKey: ["compare"] });
    },
  });

  function chooseProject(nextId) {
    setParams(nextId ? { proyecto: nextId } : {});
    setSelected(new Set());
    setRoleId("");
    preview.reset();
    apply.reset();
  }

  function toggle(folder, withChildren) {
    setSelected((current) => {
      const next = new Set(current);
      const ids = withChildren ? withDescendants(matrix.data.folders, folder.id) : [folder.id];
      const shouldSelect = ids.some((id) => !next.has(id));
      ids.forEach((id) => (shouldSelect ? next.add(id) : next.delete(id)));
      return next;
    });
    preview.reset();
    apply.reset();
  }

  const plan = apply.data || preview.data;
  const ready = (plan?.summary.new || 0) + (plan?.summary.change || 0);
  const roles = matrix.data?.roles || [];

  return (
    <>
      <PageHeader
        eyebrow="Carpetas"
        title="Permisos masivos"
        lede="Elige carpetas, un rol y el nivel. La confirmación muestra el antes y el después."
      />
      <PageState isLoading={projects.isLoading} error={projects.error}>
        <section className="panel filters">
          <label>
            Proyecto
            <select value={projectId} onChange={(event) => chooseProject(event.target.value)}>
              <option value="">Selecciona una obra</option>
              {(projects.data || []).map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Rol
            <select
              value={roleId}
              onChange={(event) => {
                setRoleId(event.target.value);
                preview.reset();
                apply.reset();
              }}
              disabled={!roles.length}
            >
              <option value="">Selecciona un rol</option>
              {roles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Nivel
            <select
              value={level}
              onChange={(event) => {
                setLevel(event.target.value);
                preview.reset();
                apply.reset();
              }}
            >
              {LEVELS.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        </section>

        {projectId ? (
          <PageState isLoading={matrix.isLoading} error={matrix.error}>
            {matrix.data ? (
              <section className="split">
                <div className="panel">
                  <div className="panel-head">
                    <h2>Carpetas</h2>
                    <button type="button" className="text-button" onClick={() => setSelected(new Set())}>
                      Limpiar
                    </button>
                  </div>
                  <ul className="check-list">
                    {matrix.data.folders.map((folder) => (
                      <li key={folder.id} style={{ paddingLeft: 12 + folder.depth * 18 }}>
                        <label>
                          <input
                            type="checkbox"
                            checked={selected.has(folder.id)}
                            onChange={() => toggle(folder, false)}
                          />
                          <span>{folder.name}</span>
                        </label>
                        {folder.depth === 0 ? (
                          <button type="button" className="text-button" onClick={() => toggle(folder, true)}>
                            Con subcarpetas
                          </button>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                  <button
                    type="button"
                    className="button"
                    disabled={selected.size === 0 || !roleId || preview.isPending}
                    onClick={() => preview.mutate(payload)}
                  >
                    {preview.isPending ? "Revisando…" : "Vista previa"}
                  </button>
                </div>
                <div className="panel">
                  <div className="panel-head">
                    <h2>{apply.data ? "Resultado" : "Antes y después"}</h2>
                    {plan ? (
                      <button
                        type="button"
                        className="button"
                        disabled={ready === 0 || apply.isPending || Boolean(apply.data)}
                        onClick={() => apply.mutate(payload)}
                      >
                        {apply.isPending ? "Aplicando…" : `Confirmar ${ready}`}
                      </button>
                    ) : null}
                  </div>
                  {preview.isError ? <p className="state state-error">{preview.error.message}</p> : null}
                  {apply.isError ? <p className="state state-error">{apply.error.message}</p> : null}
                  {!plan ? <p className="state">Selecciona carpetas y pide la vista previa.</p> : null}
                  {plan ? (
                    <>
                      {apply.data ? (
                        <p className="confirm-note">
                          Permisos actualizados. <Link to={`/proyectos/${projectId}`}>Ver la tabla</Link>
                        </p>
                      ) : null}
                      <div className="table-wrap">
                        <table>
                          <caption className="sr-only">Cambios de permiso propuestos</caption>
                          <thead>
                            <tr>
                              <th>Carpeta</th>
                              <th>Antes</th>
                              <th>Después</th>
                              <th>Estado</th>
                            </tr>
                          </thead>
                          <tbody>
                            {plan.rows.map((row) => (
                              <tr key={row.folder_id}>
                                <td>{row.path}</td>
                                <td>
                                  <LevelPill level={row.level_before} />
                                </td>
                                <td>
                                  <LevelPill level={row.level_after} />
                                </td>
                                <td>
                                  <Tag kind={row.status} map="permission" />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  ) : null}
                </div>
              </section>
            ) : null}
          </PageState>
        ) : (
          <p className="state">Elige un proyecto para ver sus carpetas.</p>
        )}
      </PageState>
    </>
  );
}
