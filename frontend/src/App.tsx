import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Layout } from "./components/layout/Layout";
import { OverviewPage } from "./features/dashboard/OverviewPage";
import { ExperimentsPage } from "./features/experiments/ExperimentsPage";
import { AuditTrailPage } from "./features/audit/AuditTrailPage";
import { SyntheticSandboxPage } from "./features/sandbox/SyntheticSandboxPage";
import { PoliciesPage } from "./features/policies/PoliciesPage";
import { ReportsPage } from "./features/reports/ReportsPage";
import { SettingsPage } from "./features/settings/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5000,
    },
  },
});

import { AuthProvider } from "./context/AuthContext";

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<OverviewPage />} />
              <Route path="experiments" element={<ExperimentsPage />} />
              <Route path="audit" element={<AuditTrailPage />} />
              <Route path="sandbox" element={<SyntheticSandboxPage />} />
              <Route path="policies" element={<PoliciesPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
