import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../services/api";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import { formatDate } from "../../lib/utils";
import {
  FlaskConical,
  ShieldCheck,
  AlertTriangle,
  FileCheck2,
  Sliders,
  ArrowRight,
  ShieldAlert,
  Activity,
  CheckCircle2,
  Clock,
  Layers
} from "lucide-react";

export const OverviewPage: React.FC = () => {
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: api.getDashboardSummary,
    refetchInterval: 5000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3 text-slate-500">
          <Activity className="w-8 h-8 animate-spin text-bayora-primary" />
          <span className="text-sm font-medium">Aggregating live telemetry...</span>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="p-6 rounded-xl bg-rose-50 border border-rose-200 text-rose-800">
        <h3 className="font-heading font-semibold text-lg">Unable to load dashboard metrics</h3>
        <p className="text-sm mt-1">Please ensure the Bayora backend engine is running on port 8000.</p>
      </div>
    );
  }

  const {
    total_experiments = 0,
    total_findings = 0,
    findings_by_severity = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 },
    avg_risk_score = 0,
    recent_experiments = [],
    recent_audit_events = [],
    active_policies_count = 0,
  } = summary;

  return (
    <div className="space-y-8">
      {/* Welcome & Problem Statement Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white p-8 shadow-md">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/15 text-cyan-300 text-xs font-medium mb-3">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>HACK IN HILLS ’26 • Problem Statement 04</span>
          </div>
          <h1 className="font-heading text-2xl lg:text-3xl font-bold tracking-tight text-white">
            Bayora Isolation Lab
          </h1>
          <p className="mt-2 text-sm text-slate-300 leading-relaxed">
            Evidence-based security validation platform for adversarial AI testing infrastructure.
            Verify tenant separation, session isolation boundaries, forensic audit chains, and configuration risks with zero simulated claims.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Link to="/experiments?new=true">
              <Button size="md" className="bg-gradient-to-r from-bayora-cyan to-bayora-primary text-white font-semibold shadow-md hover:opacity-95">
                <FlaskConical className="w-4 h-4 mr-2" />
                Launch Validation Run
              </Button>
            </Link>
            <Link to="/sandbox">
              <Button variant="outline" size="md" className="bg-white/10 border-white/20 text-white hover:bg-white/20">
                <Layers className="w-4 h-4 mr-2" />
                Run Synthetic Sandbox Adapter
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Total Validations</span>
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
              <FlaskConical className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-heading text-slate-900">{total_experiments}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Historical experiment runs</div>
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Security Findings</span>
            <div className="p-2 rounded-lg bg-rose-50 text-rose-600">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-heading text-slate-900">{total_findings}</div>
            <div className="text-[11px] text-rose-600 font-medium mt-0.5">
              {findings_by_severity.CRITICAL} Critical • {findings_by_severity.HIGH} High
            </div>
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Average Risk Score</span>
            <div className="p-2 rounded-lg bg-amber-50 text-amber-600">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-heading text-slate-900">
              {avg_risk_score.toFixed(1)} <span className="text-xs font-normal text-slate-400">/ 100</span>
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">Across completed evaluations</div>
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Active Policies</span>
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
              <Sliders className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-heading text-slate-900">{active_policies_count}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Baseline & custom rules enforced</div>
          </div>
        </Card>
      </div>

      {/* Findings Breakdown by Severity */}
      <Card>
        <CardHeader>
          <CardTitle>Findings Distribution by Severity</CardTitle>
          <span className="text-xs text-slate-400">Ground-truth evidence counts</span>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[
              { label: "Critical", count: findings_by_severity.CRITICAL, variant: "CRITICAL" as const, bg: "bg-rose-50 border-rose-200 text-rose-700" },
              { label: "High", count: findings_by_severity.HIGH, variant: "HIGH" as const, bg: "bg-orange-50 border-orange-200 text-orange-700" },
              { label: "Medium", count: findings_by_severity.MEDIUM, variant: "MEDIUM" as const, bg: "bg-amber-50 border-amber-200 text-amber-700" },
              { label: "Low", count: findings_by_severity.LOW, variant: "LOW" as const, bg: "bg-blue-50 border-blue-200 text-blue-700" },
              { label: "Info", count: findings_by_severity.INFO, variant: "INFO" as const, bg: "bg-slate-50 border-slate-200 text-slate-700" },
            ].map((s) => (
              <div key={s.label} className={`p-4 rounded-xl border ${s.bg} flex flex-col justify-between`}>
                <span className="text-xs font-semibold uppercase tracking-wider">{s.label}</span>
                <span className="text-3xl font-heading font-bold mt-2">{s.count}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Two Column Layout: Recent Experiments & Audit Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Experiments (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Validation Runs</CardTitle>
              <Link to="/experiments" className="text-xs font-medium text-bayora-primary hover:underline flex items-center gap-1">
                View all <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </CardHeader>
            <div className="divide-y divide-slate-100">
              {recent_experiments.length === 0 ? (
                <div className="p-8 text-center">
                  <FlaskConical className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                  <p className="text-sm font-medium text-slate-600">No experiments executed yet</p>
                  <p className="text-xs text-slate-400 mt-1">Start by uploading a test configuration or artifact.</p>
                  <Link to="/experiments?new=true" className="inline-block mt-4">
                    <Button size="sm">Create First Experiment</Button>
                  </Link>
                </div>
              ) : (
                recent_experiments.map((exp) => (
                  <div key={exp.id} className="p-4 sm:px-6 flex items-center justify-between hover:bg-slate-50/60 transition-colors">
                    <div className="min-w-0 pr-4">
                      <div className="flex items-center gap-2">
                        <span className="font-heading font-semibold text-sm text-slate-900 truncate">
                          {exp.name}
                        </span>
                        <Badge variant={exp.risk_level} size="sm">
                          {exp.risk_level}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                        <span className="capitalize">{exp.operation.replace("_", " ")}</span>
                        <span>•</span>
                        <span className="font-mono text-[11px]">{exp.artifact_filename}</span>
                        <span>•</span>
                        <span>{formatDate(exp.created_at)}</span>
                      </div>
                    </div>
                    <Link to={`/experiments?runId=${exp.id}`}>
                      <Button variant="outline" size="sm">
                        View Findings
                      </Button>
                    </Link>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        {/* Recent Audit Activity (1 Col) */}
        <div>
          <Card className="h-full flex flex-col">
            <CardHeader>
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-slate-600" />
                <CardTitle>Tamper-Evident Audit</CardTitle>
              </div>
              <Link to="/audit" className="text-xs font-medium text-bayora-primary hover:underline">
                Audit Trail
              </Link>
            </CardHeader>
            <div className="p-4 flex-1 divide-y divide-slate-100 overflow-y-auto max-h-[380px]">
              {recent_audit_events.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-xs">
                  No audit events recorded.
                </div>
              ) : (
                recent_audit_events.map((evt) => (
                  <div key={evt.id} className="py-2.5 first:pt-0 last:pb-0 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-medium text-slate-800 text-[11px]">
                        {evt.event_type}
                      </span>
                      <span className="text-[10px] text-slate-400">{formatDate(evt.timestamp)}</span>
                    </div>
                    <div className="flex items-center justify-between mt-1 text-[11px] text-slate-500">
                      <span>Actor: <strong className="text-slate-700">{evt.actor}</strong></span>
                      <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                        {evt.record_hash}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
