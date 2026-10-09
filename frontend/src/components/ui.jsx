export function PageState({ isLoading, error, children }) {
  if (isLoading) return <p className="state">Cargando…</p>;
  if (error) return <p className="state state-error">{error.message}</p>;
  return children;
}

export function PageHeader({ eyebrow, title, lede, actions }) {
  return (
    <header className="page-header">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {lede ? <p className="lede">{lede}</p> : null}
      </div>
      {actions ? <div className="header-actions">{actions}</div> : null}
    </header>
  );
}

const LEVEL_LABEL = {
  ver: "Ver",
  descargar: "Descargar",
  editar: "Editar",
  administrar: "Administrar",
};

export function LevelPill({ level }) {
  if (!level) return <span className="level level-empty">Sin permiso</span>;
  return <span className={`level level-${level}`}>{LEVEL_LABEL[level] || level}</span>;
}

const MEMBERSHIP_TAG = {
  applicable: ["tag-ok", "Se aplicará"],
  update_role: ["tag-warn", "Cambia el rol"],
  already_member: ["tag-muted", "Ya es miembro"],
  incomplete: ["tag-bad", "Incompleta"],
  invalid_email: ["tag-bad", "Correo inválido"],
  unknown_role: ["tag-bad", "Rol desconocido"],
  unknown_project: ["tag-bad", "Proyecto desconocido"],
  simulated_error: ["tag-bad", "Error simulado"],
};

const PERMISSION_TAG = {
  new: ["tag-ok", "Nuevo"],
  change: ["tag-warn", "Cambia"],
  unchanged: ["tag-muted", "Sin cambio"],
  rejected: ["tag-bad", "Rechazada"],
};

export function Tag({ kind, map = "membership" }) {
  const source = map === "permission" ? PERMISSION_TAG : MEMBERSHIP_TAG;
  const [tone, label] = source[kind] || ["tag-muted", kind];
  return <span className={`tag ${tone}`}>{label}</span>;
}

export function formatDate(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "long",
    timeZone: "UTC",
  }).format(new Date(value));
}

export function formatWhen(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function statusClass(status) {
  if (status === "En obra") return "chip chip-live";
  if (status === "En diseño") return "chip chip-plan";
  return "chip";
}
