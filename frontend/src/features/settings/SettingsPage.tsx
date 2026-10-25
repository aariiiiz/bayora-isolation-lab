import React, { useState } from "react";
import { api, authStorage } from "../../services/api";
import { useAuth } from "../../context/AuthContext";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import {
  Sliders,
  Shield,
  Lock,
  Database,
  Cpu,
  CheckCircle2,
  AlertCircle,
  Key,
  Layers,
  FileCode,
  RefreshCw,
  ExternalLink
} from "lucide-react";

export const SettingsPage: React.FC = () => {
  const { user, activeTenant } = useAuth();
  const token = authStorage.getToken();
  const [testingEngine, setTestingEngine] = useState(false);
  const [engineHealth, setEngineHealth] = useState<any>(null);

  const checkHealth = async () => {
    setTestingEngine(true);
    try {
      const res = await fetch("http://localhost:8000/api/health");
      const data = await res.json();
      setEngineHealth(data);
    } catch (e) {
      setEngineHealth({ status: "error", error: (e as Error).message });
    } finally {
      setTestingEngine(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl text-slate-900">
            Platform Settings & Isolation Architecture
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            System configuration, cryptographic ledger parameters, and tenant boundary enforcement policies.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={checkHealth}
          isLoading={testingEngine}
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Verify Engine Health
        </Button>
      </div>

      {engineHealth && (
        <div className={`p-4 rounded-xl border text-xs ${
          engineHealth.status === "ok"
            ? "bg-emerald-50 border-emerald-200 text-emerald-900"
            : "bg-rose-50 border-rose-200 text-rose-900"
        }`}>
          <div className="flex items-center gap-2 font-semibold">
            {engineHealth.status === "ok" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600" />
            )}
            <span>Engine Diagnostic: {engineHealth.status?.toUpperCase() || "ERROR"}</span>
          </div>
          <div className="mt-1 font-mono text-[11px]">
            Platform: {engineHealth.platform || "Bayora Isolation Lab"} • Version: {engineHealth.version || "1.0.0"} • Timestamp: {engineHealth.timestamp || new Date().toISOString()}
          </div>
        </div>
      )}

      {/* Grid: 2 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tenant Boundary Security */}
        <Card className="p-6">
          <div className="flex items-center gap-2.5 mb-4">
            <div className="p-2 rounded-lg bg-blue-50 text-bayora-primary">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-heading font-semibold text-base text-slate-900">
                Tenant Partitioning & Boundary Enforcement
              </h3>
              <p className="text-xs text-slate-500">Row-level isolation and egress filtering</p>
            </div>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="font-medium text-slate-700">Active Tenant Context</span>
              <span className="font-mono font-bold text-slate-900">{activeTenant?.id || "tenant-alpha"}</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="font-medium text-slate-700">Isolation Mode</span>
              <span className="inline-flex items-center gap-1.5 font-semibold text-emerald-700">
                <CheckCircle2 className="w-3.5 h-3.5" /> Strict Server-Enforced Partitioning
              </span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="font-medium text-slate-700">IDOR Prevention Barrier</span>
              <span className="font-semibold text-emerald-700">Active (404 Non-Disclosing Egress)</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="font-medium text-slate-700">Cross-Tenant Storage Partition</span>
              <span className="font-mono text-[11px] text-slate-600">/tenants/&#123;tenant_id&#125;/experiments</span>
            </div>
          </div>
        </Card>

        {/* Cryptographic Ledger Parameters */}
        <Card className="p-6">
          <div className="flex items-center gap-2.5 mb-4">
            <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-heading font-semibold text-base text-slate-900">
                Tamper-Evident Ledger Parameters
              </h3>
              <p className="text-xs text-slate-500">Cryptographic audit chain specifications</p>
            </div>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="font-medium text-slate-700">Cryptographic Hash Algorithm</span>
              <span className="font-mono font-bold text-slate-900">SHA-256 (256-bit Digest)</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="font-medium text-slate-700">Serialization Standard</span>
              <span className="font-mono font-bold text-slate-900">RFC-8785 Canonical JSON</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="font-medium text-slate-700">Sequence Verification</span>
              <span className="font-semibold text-indigo-700">Tenant-Scoped Monotonic (Strict)</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="font-medium text-slate-700">External Checkpoint Anchor</span>
              <span className="font-mono text-[11px] text-slate-600">.audit_checkpoint.json (OS Filesystem)</span>
            </div>
          </div>
        </Card>

        {/* Role-Based Access Control (RBAC) */}
        <Card className="p-6">
          <div className="flex items-center gap-2.5 mb-4">
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-heading font-semibold text-base text-slate-900">
                Role-Based Access Control (RBAC)
              </h3>
              <p className="text-xs text-slate-500">Role permissions within tenant domains</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2 px-3">Capability / Operation</th>
                  <th className="py-2 px-2 text-center">Admin</th>
                  <th className="py-2 px-2 text-center">Analyst</th>
                  <th className="py-2 px-2 text-center">Viewer</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                <tr>
                  <td className="py-2 px-3">Run & Retest Security Experiments</td>
                  <td className="py-2 px-2 text-center text-emerald-600 font-bold">✓</td>
                  <td className="py-2 px-2 text-center text-emerald-600 font-bold">✓</td>
                  <td className="py-2 px-2 text-center text-rose-500 font-bold">✕</td>
                </tr>
                <tr>
                  <td className="py-2 px-3">Inspect Findings & Export Reports</td>
                  <td className="py-2 px-2 text-center text-emerald-600 font-bold">✓</td>
                  <td className="py-2 px-2 text-center text-emerald-600 font-bold">✓</td>
                  <td className="py-2 px-2 text-center text-emerald-600 font-bold">✓</td>
                </tr>
                <tr>
                  <td className="py-2 px-3">Inspect Tamper-Evident Audit Ledger</td>
                  <td className="py-2 px-2 text-center text-emerald-600 font-bold">✓</td>
                  <td className="py-2 px-2 text-center text-emerald-600 font-bold">✓</td>
                  <td className="py-2 px-2 text-center text-emerald-600 font-bold">✓</td>
                </tr>
                <tr>
                  <td className="py-2 px-3">Mutate Baseline Policies</td>
                  <td className="py-2 px-2 text-center text-emerald-600 font-bold">✓</td>
                  <td className="py-2 px-2 text-center text-emerald-600 font-bold">✓</td>
                  <td className="py-2 px-2 text-center text-rose-500 font-bold">✕</td>
                </tr>
                <tr>
                  <td className="py-2 px-3">Delete Experiment Runs & Artifacts</td>
                  <td className="py-2 px-2 text-center text-emerald-600 font-bold">✓</td>
                  <td className="py-2 px-2 text-center text-rose-500 font-bold">✕</td>
                  <td className="py-2 px-2 text-center text-rose-500 font-bold">✕</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>

        {/* Live Identity & JWT Session Inspector */}
        <Card className="p-6">
          <div className="flex items-center gap-2.5 mb-4">
            <div className="p-2 rounded-lg bg-amber-50 text-amber-600">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-heading font-semibold text-base text-slate-900">
                Session Credential Inspector
              </h3>
              <p className="text-xs text-slate-500">Live decoded JWT claims & boundary scope</p>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <div className="p-3 rounded-lg bg-slate-900 text-slate-100 font-mono text-[11px] overflow-x-auto space-y-1">
              <div><span className="text-cyan-400">subject:</span> &quot;{user?.id}&quot;</div>
              <div><span className="text-cyan-400">email:</span> &quot;{user?.email}&quot;</div>
              <div><span className="text-cyan-400">full_name:</span> &quot;{user?.full_name}&quot;</div>
              <div><span className="text-cyan-400">tenant_id:</span> &quot;{activeTenant?.id}&quot;</div>
              <div><span className="text-cyan-400">role:</span> &quot;{activeTenant?.role}&quot;</div>
              <div><span className="text-cyan-400">algorithm:</span> &quot;HS256&quot;</div>
              <div><span className="text-cyan-400">session_ttl:</span> &quot;120 minutes&quot;</div>
            </div>
            <div className="text-[11px] text-slate-500 pt-1">
              Tokens are issued with strict tenant-scoped claims and validated on every backend invocation.
            </div>
          </div>
        </Card>
      </div>

      {/* Architectural Disclosures & Limitations Notice */}
      <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-2">
        <div className="flex items-center gap-2 font-semibold text-slate-800">
          <Layers className="w-4 h-4 text-bayora-primary" />
          <span>Bayora Trust Assumptions & Architectural Disclosures (PS-04 Compliance)</span>
        </div>
        <p className="leading-relaxed">
          1. <strong>Hash Chain Boundary:</strong> A cryptographic hash chain guarantees tamper-evidence against unprivileged actors. An adversary with full write access to the underlying storage database could theoretically recompute SHA-256 hashes from genesis. To mitigate this, Bayora anchors verify operations against external filesystem checkpoint digests.
        </p>
        <p className="leading-relaxed">
          2. <strong>Deterministic Local Execution:</strong> When external LLM advisory APIs (Groq/OpenAI) are offline or non-responsive, the system executes deterministic local safety parsers and AST checkers to provide reproducible test runs without hallucinated outputs.
        </p>
      </div>
    </div>
  );
};
