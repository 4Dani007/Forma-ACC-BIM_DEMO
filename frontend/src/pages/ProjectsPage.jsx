import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { PageHeader, PageState, statusClass } from "../components/ui";

export function ProjectsPage() {
  const projects = useQuery({ queryKey: ["projects"], queryFn: () => api("/api/projects") });
  const rows = projects.data || [];
  const folders = rows.reduce((sum, item) => sum + item.folder_count, 0);
  const members = rows.reduce((sum, item) => sum + item.member_count, 0);

  return (
    <>
      <PageHeader
        eyebrow="Cartera"
        title="Proyectos"
        lede="Tres obras ficticias con carpetas, roles y permisos listos para recorrer la demostración."
      />
      <PageState isLoading={projects.isLoading} error={projects.error}>
        <section className="stats" aria-label="Resumen">
          <article>
            <span>Proyectos</span>
            <strong>{rows.length}</strong>
          </article>
          <article>
            <span>Carpetas</span>
            <strong>{folders}</strong>
          </article>
          <article>
            <span>Asignaciones</span>
            <strong>{members}</strong>
          </article>
        </section>
        <div className="table-wrap">
          <table className="projects-table">
            <caption className="sr-only">Proyectos de la demostración</caption>
            <thead>
              <tr>
                <th>Proyecto</th>
                <th>Código</th>
                <th>Estado</th>
                <th>Ubicación</th>
                <th>Cliente</th>
                <th>Fase</th>
                <th>Carpetas</th>
                <th>Miembros</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((project) => (
                <tr key={project.id}>
                  <td>
                    <Link className="row-link" to={`/proyectos/${project.id}`}>
                      {project.name}
                    </Link>
                  </td>
                  <td className="mono">{project.code}</td>
                  <td>
                    <span className={statusClass(project.status)}>{project.status}</span>
                  </td>
                  <td>{project.location}</td>
                  <td>{project.client}</td>
                  <td>{project.phase}</td>
                  <td>{project.folder_count}</td>
                  <td>{project.member_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </PageState>
    </>
  );
}
