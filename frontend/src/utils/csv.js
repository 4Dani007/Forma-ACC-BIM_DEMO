const REQUIRED = ["nombre", "correo", "empresa", "rol", "proyectos"];

export function parseCsv(text) {
  const cleaned = text.replace(/^\uFEFF/, "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const table = [];
  let row = [];
  let cell = "";
  let quoted = false;

  for (let index = 0; index < cleaned.length; index += 1) {
    const char = cleaned[index];
    if (quoted) {
      if (char === '"') {
        if (cleaned[index + 1] === '"') {
          cell += '"';
          index += 1;
        } else {
          quoted = false;
        }
      } else {
        cell += char;
      }
      continue;
    }
    if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(cell.trim());
      cell = "";
    } else if (char === "\n") {
      row.push(cell.trim());
      cell = "";
      if (row.some(Boolean)) table.push(row);
      row = [];
    } else {
      cell += char;
    }
  }
  if (cell.length || row.length) {
    row.push(cell.trim());
    if (row.some(Boolean)) table.push(row);
  }

  if (table.length < 2) {
    throw new Error("El archivo no tiene filas para asignar.");
  }

  const headers = table[0].map((header) => header.toLocaleLowerCase("es"));
  const missing = REQUIRED.filter((column) => !headers.includes(column));
  if (missing.length) {
    throw new Error(`Faltan las columnas: ${missing.join(", ")}.`);
  }

  return table.slice(1).map((cells) => {
    const read = (column) => cells[headers.indexOf(column)] || "";
    return {
      name: read("nombre"),
      email: read("correo"),
      company: read("empresa"),
      role: read("rol"),
      projects: read("proyectos"),
    };
  });
}
