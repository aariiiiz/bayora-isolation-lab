import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../services/api";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import { SyntheticMatrixReport, SyntheticScenarioResult } from "../../types";
import {
  Cpu,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  Lock,
  Layers,
  Terminal,
  Info,
  RefreshCw,
  Clock,
  KeyRound,
  FileCheck2,
  Users
} from "lucide-react";

export const SyntheticSandboxPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [suiteReport, setSuiteReport] = useState<SyntheticMatrixReport | null>(null);

  const runMutation = useMutation({
    mutationFn: api.runSyntheticSuite,
    onSuccess: (data) => {
      setSuiteReport(data);
      queryClient.invalidateQueries({ queryKey: ["audit-trail"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PASS":
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">PASS</span>;
      case "FAIL":
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">FAIL</span>;
      case "ERROR":
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">ERROR</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-300">SKIPPED</span>;
    }
  };

  const getCategoryIcon = (testId: string) => {
    if (testId.includes("01") || testId.includes("10")) return <ShieldCheck className="w-4 h-4 text-emerald-600" />;
    if (testId.includes("02") || testId.includes("09")) return <Lock className="w-4 h-4 text-indigo-600" />;
    if (testId.includes("03")) return <Layers className="w-4 h-4 text-purple-600" />;
    if (testId.includes("08")) return <Users className="w-4 h-4 text-amber-600" />;
    return <KeyRound className="w-4 h-4 text-slate-600" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold mb-1">
            <Cpu className="w-3.5 h-3.5" />
            <span>Controlled Local Sandbox Adapter</span>
          </div>
          <h1 className="font-heading font-bold text-2xl text-slate-900">
            Synthetic Isolation Sandbox & RBAC Matrix
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Live local test fixture demonstrating deterministic cross-tenant and cross-session isolation enforcement.
            Validates partition boundaries, role permissions, and cryptographically chained audit events for every test execution.
          </p>
        </div>

        <Button
          onClick={() => runMutation.mutate()}
          isLoading={runMutation.isPending}
          className="bg-bayora-primary hover:bg-bayora-primaryHover text-white shadow-md text-xs py-2 px-4"
        >
          <Play className="w-4 h-4 mr-2" />
          Run Controlled Isolation Test Suite (10 Scenarios)
        </Button>
      </div>

      {/* Scope Disclaimer Box */}
      <div className="p-4 rounded-xl bg-slate-100 border border-slate-200/90 text-xs text-slate-600 flex items-start gap-3">
        <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="leading-relaxed">
            <strong>Security Boundary & Local Environment Notice:</strong> This sandbox demonstrates boundary enforcement
            using real cryptographic JWT signature validation, database tenant queries, role verification, and hash-chained audit logging
            between <code className="text-slate-800 font-mono font-semibold">tenant-alpha</code> and <code className="text-slate-800 font-mono font-semibold">tenant-beta</code>.
          </p>
          <p className="text-[11px] text-slate-500">
            *Results prove empirical enforcement of Bayora's software security architecture, but do not prove isolation across arbitrary external third-party infrastructure.
          </p>
        </div>
      </div>

      {/* Suite Results Summary Banner if executed */}
      {suiteReport && (
        <Card className="border-emerald-200 bg-emerald-50/30">
          <CardHeader className="bg-emerald-50/60 border-b border-emerald-100 py-3 px-5 flex flex-wrap items-center justify-between">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <CardTitle className="text-emerald-950 text-sm font-bold">
                Suite Execution Result: {suiteReport.passed_tests} / {suiteReport.total_tests} Scenarios Enforced
              </CardTitle>
            </div>
            <div className="flex items-center gap-4 text-xs font-mono text-emerald-800">
              <span>Audit Events Chained: <strong>{suiteReport.audit_events_recorded}</strong></span>
              <span>Executed: {new Date(suiteReport.executed_at).toLocaleTimeString()}</span>
            </div>
          </CardHeader>
        </Card>
      )}

      {/* 10-Scenario Matrix Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          {
            id: "ISO-TEST-01",
            title: "Authorized Same-Tenant Access",
            desc: "Valid user in Tenant Alpha requests permitted evaluation dataset with active credentials.",
            expected: "200 OK (Access Allowed)",
            category: "Identity & Scoping"
          },
          {
            id: "ISO-TEST-02",
            title: "Cross-Tenant Access Denial",
            desc: "Tenant Alpha attempts to request Tenant Beta's proprietary red-team exploit artifact.",
            expected: "403 Forbidden (Partition Enforced)",
            category: "Tenant Boundary"
          },
          {
            id: "ISO-TEST-03",
            title: "Cross-Session Memory State Isolation",
            desc: "Session 2 attempts to read private scratchpad memory of Session 1 to test conversation state leakage.",
            expected: "403 Forbidden (Session Enforced)",
            category: "Session Partition"
          },
          {
            id: "ISO-TEST-04",
            title: "Missing Identity Context Denial",
            desc: "Unauthenticated request executed with no Authorization header or token claims.",
            expected: "401 Unauthorized (Context Missing)",
            category: "Authentication"
          },
          {
            id: "ISO-TEST-05",
            title: "Invalid / Tampered Token Rejection",
            desc: "Request with spoofed tenant identifier and tampered HMAC cryptographic signature.",
            expected: "401 Unauthorized (Signature Mismatch)",
            category: "Cryptographic Tamper"
          },
          {
            id: "ISO-TEST-06",
            title: "Expired Identity Credential Rejection",
            desc: "Caller presents an expired access token beyond the valid cryptographic timestamp window.",
            expected: "401 Unauthorized (Token Expired)",
            category: "Session Lifetime"
          },
          {
            id: "ISO-TEST-07",
            title: "Missing Tenant Context / Homeless Identity",
            desc: "Authenticated user account without authorized membership in the target tenant.",
            expected: "403 Forbidden (Membership Missing)",
            category: "Tenant Membership"
          },
          {
            id: "ISO-TEST-08",
            title: "Role Privilege Escalation Denial",
            desc: "Viewer role attempts to invoke restricted administrative policy mutation API.",
            expected: "403 Forbidden (Admin Role Required)",
            category: "RBAC Authorization"
          },
          {
            id: "ISO-TEST-09",
            title: "Cross-Tenant Report Export Denial",
            desc: "Tenant Alpha analyst attempts to download security report of Tenant Beta's private run.",
            expected: "404 Not Found (Non-Disclosing IDOR)",
            category: "IDOR Prevention"
          },
          {
            id: "ISO-TEST-10",
            title: "Authorized Retest Execution with Linkage",
            desc: "Analyst initiates a linked retest run preserving parent run immutability.",
            expected: "200 OK (Retest Run Created)",
            category: "Retest Workflow"
          }
        ].map((sc) => {
          const runOutcome = suiteReport?.results?.find((r) => r.test_id === sc.id);

          return (
            <Card key={sc.id} className="p-4 flex flex-col justify-between border-slate-200 shadow-xs hover:border-slate-300 transition-all">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getCategoryIcon(sc.id)}
                    <span className="font-mono text-xs font-bold text-slate-500">{sc.id}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                      {sc.category}
                    </span>
                    {runOutcome && getStatusBadge(runOutcome.status)}
                  </div>
                </div>

                <h3 className="font-heading font-semibold text-sm text-slate-900 mb-1">{sc.title}</h3>
                <p className="text-xs text-slate-600 leading-relaxed mb-3">{sc.desc}</p>

                <div className="text-[11px] text-slate-600 font-mono bg-slate-50 p-2 rounded border border-slate-100">
                  Target: <strong className="text-slate-800">{sc.expected}</strong>
                </div>
              </div>

              {/* Execution Outcome & Evidence */}
              {runOutcome && (
                <div className="mt-3 pt-3 border-t border-slate-100 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-700">Observed Result:</span>
                    <span className="font-mono text-[11px] font-bold text-slate-800">
                      HTTP {runOutcome.status_code}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-500 italic leading-snug">
                    {runOutcome.message}
                  </p>

                  {runOutcome.audit_event_id && (
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 bg-slate-100/70 px-2 py-1 rounded">
                      <span>Audit Ref: {runOutcome.audit_event_id.substring(0, 12)}...</span>
                      <span className="text-emerald-700 font-semibold">Chained SHA-256</span>
                    </div>
                  )}
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* Raw Payload Log for Security Auditors */}
      {suiteReport && (
        <Card className="border-slate-200">
          <CardHeader className="py-3 px-5 border-b border-slate-100">
            <CardTitle className="text-xs font-mono uppercase tracking-wider text-slate-500">
              Audit Payload & Test Evidence Stream
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-3">
            <div className="p-3 bg-slate-900 text-slate-200 rounded-lg overflow-x-auto max-h-60 text-xs font-mono">
              <pre>{JSON.stringify(suiteReport, null, 2)}</pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
