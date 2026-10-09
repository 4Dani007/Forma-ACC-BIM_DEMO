import { Link } from "react-router-dom";

const ACTIONS = [
  {
    to: "/proyectos",
    title: "Ver proyectos y permisos",
    text: "Abre una obra, revisa la matriz por carpeta y rol, y descarga metadatos, CSV o Excel.",
  },
  {
    to: "/asignacion",
    title: "Asignar usuarios en lote",
    text: "Carga un CSV, mira qué pasará con cada fila y confirma. La vista previa no escribe nada.",
  },
  {
    to: "/permisos",
    title: "Cambiar permisos de varias carpetas",
    text: "Elige carpetas, un rol y un nivel. Antes de aplicar ves el permiso actual y el nuevo.",
  },
  {
    to: "/comparador",
    title: "Comparar dos obras",
    text: "Las carpetas se emparejan por ruta. El color marca permiso distinto, rol sin permiso o carpeta faltante.",
  },
  {
    to: "/registro",
    title: "Revisar el registro",
    text: "Cada asignación o cambio masivo queda anotado, con el resultado de cada fila.",
  },
];

export function WelcomePage() {
  return (
    <main className="welcome">
      <div className="welcome-brand">
        <span className="brand-mark" aria-hidden="true">
          S
        </span>
        <div>
          <strong>Senda</strong>
          <small>Permisos de obra</small>
        </div>
      </div>
      <p className="eyebrow">Demostración</p>
      <h1>Administra usuarios y permisos de carpetas sin hacerlo uno por uno.</h1>
      <p className="lede">
        Tres obras ficticias ya traen carpetas, roles y diferencias sembradas. Puedes recorrer el flujo, aplicar
        cambios y volver al estado inicial cuando quieras.
      </p>
      <ol className="welcome-actions">
        {ACTIONS.map((action, index) => (
          <li key={action.to}>
            <Link to={action.to}>
              <span>{index + 1}</span>
              <strong>{action.title}</strong>
              <p>{action.text}</p>
            </Link>
          </li>
        ))}
      </ol>
      <div className="welcome-footer">
        <Link className="button" to="/proyectos">
          Entrar a la demo
        </Link>
        <p>Los datos son ficticios y no se envían a ningún servicio externo. Si otro visitante los cambia, usa Restaurar datos de ejemplo.</p>
      </div>
    </main>
  );
}
