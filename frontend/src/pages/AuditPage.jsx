import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { PageHeader, PageState, formatWhen } from "../components/ui";

const ACTION_LABEL = {
  seed: "Datos de ejemplo",
  bulk_memberships: "Asignación masiva",
  bulk_permissions: "Permisos masivos",
};

export function AuditPage() {
  const audit = useQuery({ queryKey: ["audit"], queryFn: () => api("/api/audit") });

  return (
    <>
      <PageHeader
        eyebrow="Trazabilidad"
        title="Registro"
        lede="Cada asignación o cambio masivo queda anotado con el resultado por fila."
      />
      <PageState isLoading={audit.isLoading} error={audit.error}>
        <ol className="timeline">
          {(audit.data || []).map((entry) => (
            <li key={entry.id}>
              <div className="timeline-head">
                <strong>{ACTION_LABEL[entry.action] || entry.action}</strong>
                <time dateTime={entry.created_at}>{formatWhen(entry.created_at)}</time>
              </div>
              <p>
                {entry.actor}
                {entry.detail?.mensaje ? ` · ${entry.detail.mensaje}` : ""}
              </p>
              <Counts detail={entry.detail} />
              {Array.isArray(entry.detail?.filas) ? (
                <details>
                  <summary>{entry.detail.filas.length} filas</summary>
                  <ul>
                    {entry.detail.filas.map((row, index) => (
                      <li key={`${entry.id}-${index}`}>{row.message || row.path || row.email}</li>
                    ))}
                  </ul>
                </details>
              ) : null}
            </li>
          ))}
        </ol>
        {audit.data?.length === 0 ? <p className="state">Todavía no hay acciones.</p> : null}
      </PageState>
    </>
  );
}

function Counts({ detail }) {
  if (!detail) return null;
  const parts = [];
  if (detail.aplicadas != null) parts.push(`${detail.aplicadas} aplicadas`);
  if (detail.omitidas != null) parts.push(`${detail.omitidas} omitidas`);
  if (detail.sin_cambio != null) parts.push(`${detail.sin_cambio} sin cambio`);
  if (detail.rechazadas != null) parts.push(`${detail.rechazadas} rechazadas`);
  if (!parts.length) return null;
  return <p className="counts">{parts.join(" · ")}</p>;
}
