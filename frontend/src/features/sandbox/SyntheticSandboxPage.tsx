import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../services/api";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import {
  Cpu,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Play,
  Lock,
  Layers,
  Terminal,
  Info
} from "lucide-react";

export const SyntheticSandboxPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [suiteReport, setSuiteReport] = useState<any>(null);

  const runMutation = useMutation({
    mutationFn: api.runSyntheticSuite,
    onSuccess: (data) => {
      setSuiteReport(data);
      queryClient.invalidateQueries({ queryKey: ["audit-trail"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold mb-1">
            <Cpu className="w-3.5 h-3.5" />
            <span>Controlled Local Adapter</span>
          </div>
          <h1 className="font-heading font-bold text-2xl text-slate-900">
            Synthetic Isolation Sandbox
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Live local test fixture demonstrating deterministic cross-tenant and cross-session isolation enforcement.
            Validates partition boundaries and verifies that audit events are generated for every test outcome.
          </p>
        </div>

        <Button
          onClick={() => runMutation.mutate()}
          isLoading={runMutation.isPending}
          className="bg-bayora-primary hover:bg-bayora-primaryHover text-white shadow-md"
        >
          <Play className="w-4 h-4 mr-2" />
          Run Controlled Isolation Test Suite
        </Button>
      </div>

      {/* Scope Disclaimer Box */}
      <div className="p-4 rounded-xl bg-slate-100 border border-slate-200/90 text-xs text-slate-600 flex items-start gap-3">
        <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Security Assumption & Boundary:</strong> This adapter runs exclusively against the local in-memory synthetic fixture
          (<code className="text-slate-800 font-mono">tenant-alpha</code> and <code className="text-slate-800 font-mono">tenant-beta</code>).
          It validates isolation enforcement logic without transmitting probes to arbitrary third-party cloud endpoints.
        </p>
      </div>

      {/* Test Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          {
            id: "SYNTH-01",
            title: "Authorized In-Tenant Access",
            desc: "Tenant Alpha requests its own private evaluation dataset with valid credentials.",
            expected: "200 OK (Access Granted)",
            badge: "Authorized",
            type: "auth"
          },
          {
            id: "SYNTH-02",
            title: "Cross-Tenant Access Denial",
            desc: "Tenant Alpha attempts to access Tenant Beta's proprietary red-team exploits.",
            expected: "403 Forbidden (Partition Enforced)",
            badge: "Cross-Tenant",
            type: "boundary"
          },
          {
            id: "SYNTH-03",
            title: "Cross-Session Memory Isolation",
            desc: "Session 2 attempts to read private scratchpad memory of Session 1.",
            expected: "403 Forbidden (Session Enforced)",
            badge: "Session Boundary",
            type: "session"
          },
          {
            id: "SYNTH-04",
            title: "Missing Identity Context Rejection",
            desc: "Anonymous request executed without tenant header or authorization token.",
            expected: "401 Unauthorized (Context Missing)",
            badge: "Unauthenticated",
            type: "auth"
          },
          {
            id: "SYNTH-05",
            title: "Forged Token Signature Rejection",
            desc: "Request with spoofed tenant identifier and tampered cryptographic token.",
            expected: "401 Unauthorized (Signature Mismatch)",
            badge: "Tamper Proof",
            type: "auth"
          }
        ].map((sc) => {
          const runOutcome = suiteReport?.scenarios?.find((s: any) => s.scenario_id === sc.id);

          return (
            <Card key={sc.id} className="p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-500">{sc.id}</span>
                    <h3 className="font-heading font-semibold text-sm text-slate-900">{sc.title}</h3>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                    {sc.badge}
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed mb-3">{sc.desc}</p>
                <div className="text-[11px] text-slate-500 font-mono bg-slate-50 p-2 rounded border border-slate-100">
                  Target Outcome: <strong className="text-slate-700">{sc.expected}</strong>
                </div>
              </div>

              {/* Execution Result */}
              {runOutcome && (
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    {runOutcome.passed ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-600" />
                    )}
                    <span className="font-semibold text-slate-800">
                      {runOutcome.passed ? "Enforcement Verified" : "Violation Detected"}
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-slate-500">
                    HTTP {runOutcome.status_code}
                  </span>
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* Live Suite Execution Output */}
      {suiteReport && (
        <Card className="border-emerald-200 bg-emerald-50/20">
          <CardHeader className="bg-emerald-50/50 border-b border-emerald-100">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <CardTitle className="text-emerald-950">
                Sandbox Suite Results: {suiteReport.passed_scenarios} / {suiteReport.total_scenarios} Scenarios Enforced
              </CardTitle>
            </div>
            <span className="text-xs font-mono text-emerald-700">
              {suiteReport.audit_events_recorded} Audit Events Chained
            </span>
          </CardHeader>
          <CardContent className="space-y-3 pt-4 text-xs font-mono">
            <div className="p-3 bg-slate-900 text-slate-200 rounded-lg overflow-x-auto max-h-60">
              <pre>{JSON.stringify(suiteReport, null, 2)}</pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
