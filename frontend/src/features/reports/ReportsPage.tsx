import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../services/api";
import { Experiment } from "../../types";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import { formatDate } from "../../lib/utils";
import {
  FileText,
  Download,
  Search,
  Eye,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Calendar,
  Layers,
  Info
} from "lucide-react";

export const ReportsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedReport, setSelectedReport] = useState<any>(null);
  const [loadingReportId, setLoadingReportId] = useState<string | null>(null);

  const { data: experimentsData, isLoading } = useQuery({
    queryKey: ["reports-experiments"],
    queryFn: () => api.getExperiments({ limit: 100, status: "completed" }),
  });

  const experiments = experimentsData?.items || [];

  const filteredExperiments = experiments.filter((e) =>
    e.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.artifact_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleViewReport = async (runId: string) => {
    try {
      setLoadingReportId(runId);
      const rep = await api.getExperimentReport(runId);
      setSelectedReport(rep);
    } catch (e) {
      alert("Failed to load report: " + (e as Error).message);
    } finally {
      setLoadingReportId(null);
    }
  };

  const handleDownloadJson = async (runId: string) => {
    try {
      const rep = await api.getExperimentReport(runId);
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(rep, null, 2));
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `bayora_evaluation_${runId.slice(0, 8)}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } catch (e) {
      alert("Failed to export JSON report: " + (e as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Search */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl text-slate-900">
            Security Validation Reports
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Downloadable, formal compliance evidence artifacts and residual risk assessments.
          </p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search reports by run or artifact..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-bayora-primary/20 focus:outline-hidden"
          />
        </div>
      </div>

      {/* Reports Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-slate-500" />
            <CardTitle>Evaluation Artifacts ({filteredExperiments.length})</CardTitle>
          </div>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Experiment Name</th>
                <th className="py-3 px-4">Run Identifier</th>
                <th className="py-3 px-4">Operation</th>
                <th className="py-3 px-4">Completed Date</th>
                <th className="py-3 px-4">Severity Profile</th>
                <th className="py-3 px-4">Risk Level</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading reports...
                  </td>
                </tr>
              ) : filteredExperiments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No completed reports found.
                  </td>
                </tr>
              ) : (
                filteredExperiments.map((exp) => (
                  <tr key={exp.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      {exp.name}
                      <span className="block text-[10px] text-slate-400 font-normal">
                        {exp.artifact_filename}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-500">
                      {exp.id.slice(0, 13)}...
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-700 capitalize">
                      {exp.operation.replace("_", " ")}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 whitespace-nowrap">
                      {formatDate(exp.updated_at || exp.created_at)}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5 font-mono text-[10px]">
                        <span className="px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-bold">
                          {exp.summary?.critical || 0}C
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-orange-50 text-orange-700 border border-orange-200 font-bold">
                          {exp.summary?.high || 0}H
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-bold">
                          {exp.summary?.medium || 0}M
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge variant={exp.risk_level} size="sm">
                        {exp.risk_level} ({exp.risk_score.toFixed(0)})
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewReport(exp.id)}
                          isLoading={loadingReportId === exp.id}
                        >
                          <Eye className="w-3.5 h-3.5 mr-1" /> View
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleDownloadJson(exp.id)}
                        >
                          <Download className="w-3.5 h-3.5 mr-1" /> JSON
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* View Report Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[85vh] flex flex-col overflow-hidden border border-slate-200">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-5 h-5 text-bayora-primary" />
                <div>
                  <h3 className="font-heading font-semibold text-base text-slate-900">
                    {selectedReport.report_id} • Evaluation Report
                  </h3>
                  <span className="text-[11px] text-slate-500 font-mono">
                    Generated: {selectedReport.generated_at} • {selectedReport.platform} v{selectedReport.platform_version}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedReport(null)}
                className="text-slate-400 hover:text-slate-700 font-bold"
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5 text-xs">
              {/* Compliance & Audit Chain Status */}
              <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-emerald-950">
                    Audit Ledger Chain Status: {selectedReport.audit_chain_status}
                  </div>
                  <div className="text-[11px] text-emerald-800 mt-0.5">
                    {selectedReport.compliance_notes}
                  </div>
                </div>
              </div>

              {/* Experiment Metadata */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
                <div>
                  <span className="text-slate-400 text-[10px] uppercase font-bold block">Target</span>
                  <span className="font-semibold text-slate-800">{selectedReport.experiment.name}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] uppercase font-bold block">Environment</span>
                  <span className="font-mono text-slate-800">{selectedReport.experiment.environment}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] uppercase font-bold block">Risk Level</span>
                  <Badge variant={selectedReport.experiment.risk_level} size="sm">
                    {selectedReport.experiment.risk_level} ({selectedReport.experiment.risk_score}/100)
                  </Badge>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] uppercase font-bold block">Findings</span>
                  <span className="font-bold text-slate-900">{selectedReport.findings_count} total</span>
                </div>
              </div>

              {/* Findings Summary Table */}
              <div>
                <h4 className="font-heading font-semibold text-sm text-slate-900 mb-2">
                  Documented Findings Summary
                </h4>
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-[11px]">
                    <thead className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-2 px-3">Rule ID</th>
                        <th className="py-2 px-3">Severity</th>
                        <th className="py-2 px-3">Finding Title</th>
                        <th className="py-2 px-3">Detection</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedReport.findings.map((f: any) => (
                        <tr key={f.id}>
                          <td className="py-2 px-3 font-mono font-bold text-slate-700">{f.rule_id}</td>
                          <td className="py-2 px-3">
                            <Badge variant={f.severity} size="sm">{f.severity}</Badge>
                          </td>
                          <td className="py-2 px-3 font-medium text-slate-900">{f.title}</td>
                          <td className="py-2 px-3 font-mono text-slate-500">{f.detection_method}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Residual Risks & Limitations */}
              <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200">
                <div className="flex items-center gap-2 mb-2 font-semibold text-amber-950">
                  <Info className="w-4 h-4 text-amber-600" />
                  <span>Limitations & Residual Risk Disclosure:</span>
                </div>
                <ul className="list-disc list-inside space-y-1 text-[11px] text-amber-900 leading-relaxed">
                  {selectedReport.limitations_and_residual_risks.map((l: string, i: number) => (
                    <li key={i}>{l}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
              <span className="text-[11px] text-slate-500 font-mono">
                Cryptographically certified by Bayora Engine
              </span>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => setSelectedReport(null)}>
                  Close
                </Button>
                <Button size="sm" onClick={() => handleDownloadJson(selectedReport.experiment.id)}>
                  <Download className="w-3.5 h-3.5 mr-1" /> Download JSON
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
