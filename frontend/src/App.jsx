import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AuditPage } from "./pages/AuditPage";
import { BulkAssignPage } from "./pages/BulkAssignPage";
import { BulkPermissionsPage } from "./pages/BulkPermissionsPage";
import { ComparePage } from "./pages/ComparePage";
import { ProjectDetailPage } from "./pages/ProjectDetailPage";
import { ProjectsPage } from "./pages/ProjectsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ProjectsPage />} />
        <Route path="proyectos/:projectId" element={<ProjectDetailPage />} />
        <Route path="asignacion" element={<BulkAssignPage />} />
        <Route path="permisos" element={<BulkPermissionsPage />} />
        <Route path="comparador" element={<ComparePage />} />
        <Route path="registro" element={<AuditPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
