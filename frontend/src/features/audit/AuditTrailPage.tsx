import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../services/api";
import { AuditEvent, AuditVerificationReport } from "../../types";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import { formatDate } from "../../lib/utils";
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertOctagon,
  Terminal,
  Activity,
  Search,
  Hash,
  Link as LinkIcon,
  Copy,
  Check,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Info,
  Bug
} from "lucide-react";

export const AuditTrailPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [verificationResult, setVerificationResult] = useState<AuditVerificationReport | null>(null);
  const [demoMessage, setDemoMessage] = useState<string | null>(null);

  const { data: auditData, isLoading, refetch } = useQuery({
    queryKey: ["audit-trail"],
    queryFn: () => api.getAuditEvents({ limit: 100 }),
    refetchInterval: 6000,
  });

  const verifyMutation = useMutation({
    mutationFn: api.verifyAuditChain,
    onSuccess: (data) => {
      setVerificationResult(data);
    },
  });

  const tamperMutation = useMutation({
    mutationFn: (type: "payload" | "broken_link" | "sequence_gap") => api.simulateAuditTampering(type),
    onSuccess: (data) => {
      setDemoMessage(data.message);
      queryClient.invalidateQueries({ queryKey: ["audit-trail"] });
      // Automatically trigger chain verification to show tamper evidence
      verifyMutation.mutate();
    },
  });

  const restoreMutation = useMutation({
    mutationFn: api.restoreAuditChain,
    onSuccess: (data) => {
      setDemoMessage(data.message);
      queryClient.invalidateQueries({ queryKey: ["audit-trail"] });
      // Automatically re-verify chain to show clean state
      verifyMutation.mutate();
    },
  });

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const events = auditData?.items || [];

  return (
    <div className="space-y-6">
      {/* Page Title & Cryptographic Verification Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl text-slate-900">
            Tamper-Evident Audit Trail
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Sequential non-repudiation ledger bound by cryptographic SHA-256 hash chaining and external anchor checkpoints.
          </p>
        </div>

        <Button
          onClick={() => verifyMutation.mutate()}
          isLoading={verifyMutation.isPending}
          className="bg-slate-900 hover:bg-slate-800 text-white shadow-md focus-visible:ring-2 focus-visible:ring-bayora-primary"
        >
          <ShieldCheck className="w-4 h-4 mr-2 text-cyan-400" />
          Verify Cryptographic Chain Integrity
        </Button>
      </div>

      {/* Verification Result Banner with Detailed Evidence */}
      {verificationResult && (
        <div
          className={`p-5 rounded-2xl border transition-all ${
            verificationResult.valid
              ? "bg-emerald-50/90 border-emerald-300 text-emerald-950 shadow-sm"
              : "bg-rose-50 border-rose-300 text-rose-950 shadow-md"
          }`}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3.5">
              {verificationResult.valid ? (
                <div className="p-2 rounded-xl bg-emerald-100 text-emerald-700 shrink-0 mt-0.5">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
              ) : (
                <div className="p-2 rounded-xl bg-rose-100 text-rose-700 shrink-0 mt-0.5">
                  <AlertOctagon className="w-6 h-6 animate-pulse" />
                </div>
              )}
              <div className="space-y-2">
                <div>
                  <div className="font-heading font-bold text-base flex items-center gap-2">
                    <span>
                      {verificationResult.valid
                        ? "Cryptographic Chain Integrity Verified (Zero Tampering Detected)"
                        : "Cryptographic Tampering Detected!"}
                    </span>
                    {verificationResult.failure_category && (
                      <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-rose-200 text-rose-900 font-bold border border-rose-300">
                        {verificationResult.failure_category}
                      </span>
                    )}
                  </div>
                  <p className="text-xs mt-1 text-slate-700 leading-relaxed font-medium">
                    {verificationResult.message}
                  </p>
                </div>

                {/* Granular Evidence Breakdown on Tamper Detection */}
                {!verificationResult.valid && (
                  <div className="p-3.5 rounded-xl bg-white border border-rose-200 space-y-2 text-xs font-mono">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                      {verificationResult.event_id && (
                        <div>
                          <span className="text-slate-400 block text-[10px] uppercase">First Inconsistent Event</span>
                          <span className="font-bold text-slate-800">
                            ID: {verificationResult.event_id} (Index: #{verificationResult.broken_index ?? 0})
                          </span>
                        </div>
                      )}
                      {verificationResult.verification_timestamp && (
                        <div>
                          <span className="text-slate-400 block text-[10px] uppercase">Verification Timestamp</span>
                          <span className="text-slate-700">{verificationResult.verification_timestamp}</span>
                        </div>
                      )}
                    </div>

                    {verificationResult.expected_hash && (
                      <div className="pt-1.5 border-t border-slate-100">
                        <span className="text-slate-500 block text-[10px] uppercase font-semibold">Expected Valid Hash (SHA-256)</span>
                        <div className="flex items-center gap-2 mt-0.5 text-emerald-800 font-semibold break-all text-[11px] bg-emerald-50 px-2 py-1 rounded">
                          <span>{verificationResult.expected_hash}</span>
                        </div>
                      </div>
                    )}

                    {verificationResult.calculated_hash && (
                      <div className="pt-1.5 border-t border-slate-100">
                        <span className="text-slate-500 block text-[10px] uppercase font-semibold">Stored / Discrepant Hash</span>
                        <div className="flex items-center gap-2 mt-0.5 text-rose-800 font-semibold break-all text-[11px] bg-rose-50 px-2 py-1 rounded">
                          <span>{verificationResult.calculated_hash}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Valid Chain Metadata */}
                {verificationResult.valid && verificationResult.latest_hash && (
                  <div className="font-mono text-[11px] text-emerald-900/80 flex flex-wrap gap-4 pt-1">
                    <span>Events Verified: <strong>{verificationResult.total_verified}</strong></span>
                    <span>Anchor Checkpoint: {verificationResult.checkpoint_status?.verified ? "Verified against external anchor" : "Intact local ledger"}</span>
                    <span className="truncate max-w-xs">Chain Head: {verificationResult.latest_hash.slice(0, 20)}...</span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex flex-col items-end gap-2 shrink-0">
              <button
                onClick={() => setVerificationResult(null)}
                className="text-xs text-slate-400 hover:text-slate-700 font-semibold px-2 py-1"
                aria-label="Dismiss verification alert"
              >
                ✕ Dismiss
              </button>
              {!verificationResult.valid && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => restoreMutation.mutate()}
                  isLoading={restoreMutation.isPending}
                  className="bg-white border-rose-300 text-rose-800 hover:bg-rose-50 text-xs"
                >
                  <RotateCcw className="w-3.5 h-3.5 mr-1" />
                  Restore Ledger
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Hackathon Judge Interactive Demonstration Lab */}
      <Card className="border-indigo-100 bg-gradient-to-r from-indigo-50/40 via-purple-50/20 to-white">
        <CardHeader className="py-3.5 px-5 border-b border-indigo-100/60">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <CardTitle className="text-xs font-bold text-indigo-950 uppercase tracking-wider">
                Interactive Tamper-Evidence Demonstration Lab
              </CardTitle>
            </div>
            <span className="text-[10px] font-mono bg-white px-2 py-0.5 rounded border border-indigo-200 text-indigo-700 font-semibold">
              Adversarial Integrity Harness
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-5 space-y-4">
          <p className="text-xs text-slate-600 leading-relaxed">
            Test Bayora’s forensic verification engine against simulated adversarial database tampering.
            Simulate an attacker mutating a stored audit record payload, breaking a link, or inserting a sequence gap, then run chain verification to observe forensic tamper evidence.
          </p>

          <div className="flex flex-wrap items-center gap-2.5">
            <Button
              size="sm"
              variant="outline"
              onClick={() => tamperMutation.mutate("payload")}
              isLoading={tamperMutation.isPending}
              className="bg-white border-amber-300 text-amber-900 hover:bg-amber-50 text-xs"
            >
              <Bug className="w-3.5 h-3.5 mr-1.5 text-amber-600" />
              Simulate Payload Mutation
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => tamperMutation.mutate("broken_link")}
              isLoading={tamperMutation.isPending}
              className="bg-white border-rose-300 text-rose-900 hover:bg-rose-50 text-xs"
            >
              <LinkIcon className="w-3.5 h-3.5 mr-1.5 text-rose-600" />
              Simulate Broken Hash Link
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => restoreMutation.mutate()}
              isLoading={restoreMutation.isPending}
              className="bg-white border-emerald-300 text-emerald-900 hover:bg-emerald-50 text-xs"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1.5 text-emerald-600" />
              Restore Cryptographic Integrity
            </Button>
          </div>

          {demoMessage && (
            <div className="p-2.5 rounded-lg bg-indigo-50/80 border border-indigo-200 text-indigo-900 text-xs font-mono flex items-center justify-between">
              <span>{demoMessage}</span>
              <button
                type="button"
                onClick={() => setDemoMessage(null)}
                className="text-[10px] text-indigo-500 hover:text-indigo-800 underline ml-2 shrink-0"
              >
                Clear
              </button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Audit Events Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Hash className="w-4 h-4 text-slate-500" />
            <CardTitle>Chained Audit Records ({auditData?.total || 0})</CardTitle>
          </div>
          <span className="text-xs text-slate-400">Canonical JSON + SHA-256</span>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-200">
              <tr>
                <th className="py-3 px-3">Seq #</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Prev Hash Link</th>
                <th className="py-3 px-4">Record SHA-256 Hash</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading audit trail ledger...
                  </td>
                </tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No audit events recorded yet.
                  </td>
                </tr>
              ) : (
                events.map((evt) => {
                  const isTamperedRow =
                    verificationResult &&
                    !verificationResult.valid &&
                    (verificationResult.event_id === evt.id ||
                      (verificationResult.latest_sequence !== undefined &&
                        verificationResult.latest_sequence === evt.sequence_number));

                  return (
                    <tr
                      key={evt.id}
                      className={`transition-colors ${
                        isTamperedRow ? "bg-rose-50/80 hover:bg-rose-100/70" : "hover:bg-slate-50/70"
                      }`}
                    >
                      <td className="py-3 px-3 font-mono font-bold text-[11px] text-slate-500">
                        #{evt.sequence_number ?? 1}
                      </td>
                      <td className="py-3 px-4 text-slate-500 whitespace-nowrap">
                        {formatDate(evt.timestamp)}
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-900 font-mono text-[11px]">
                        <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                          {evt.event_type}
                        </span>
                        {isTamperedRow && (
                          <span className="ml-2 px-1.5 py-0.2 rounded bg-rose-100 text-rose-700 font-bold border border-rose-300 text-[10px]">
                            COMPROMISED
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-800">{evt.actor}</td>
                      <td className="py-3 px-4 font-mono text-[10px] text-slate-400 truncate max-w-[130px]">
                        {evt.prev_hash === "GENESIS" ? (
                          <span className="text-indigo-600 font-bold">GENESIS</span>
                        ) : (
                          evt.prev_hash.slice(0, 14) + "..."
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-[10px] text-slate-800">
                        <div className="flex items-center gap-1.5">
                          <span className="truncate max-w-[140px]">{evt.record_hash.slice(0, 16)}...</span>
                          <button
                            onClick={() => handleCopy(evt.record_hash)}
                            className="p-1 text-slate-400 hover:text-slate-700"
                            title="Copy SHA-256 Hash"
                          >
                            {copiedHash === evt.record_hash ? (
                              <Check className="w-3 h-3 text-emerald-500" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setSelectedEvent(evt)}
                          className="text-bayora-primary font-medium hover:underline text-xs"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Documented Security Boundary & Limitations Notice */}
      <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-600 flex items-start gap-3">
        <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-slate-800">
            Cryptographic Integrity & Architectural Limitations:
          </p>
          <p className="leading-relaxed text-[11px] text-slate-600">
            SHA-256 hash chaining provides tamper-evidence against record payload alterations, single-record deletions, reordering, and link breaks.
            However, a cryptographic hash chain alone cannot prevent an attacker with full root access to the database from rewriting the entire chain from genesis.
            Bayora mitigates complete rewrite attacks via local external checkpoint anchors (<code className="font-mono text-slate-800">.audit_checkpoint.json</code>), but does not claim absolute tamper-proof guarantees without multi-party consensus or hardware-enforced write-once storage (WORM).
          </p>
        </div>
      </div>

      {/* Inspect Event Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-heading font-semibold text-base text-slate-900">
                Audit Event Inspection
              </h3>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>
            <div className="p-6 space-y-4 text-xs font-mono">
              <div>
                <span className="text-slate-400 uppercase text-[10px] block">Event ID</span>
                <span className="text-slate-800 font-semibold">{selectedEvent.id}</span>
              </div>
              <div>
                <span className="text-slate-400 uppercase text-[10px] block">Sequence Number</span>
                <span className="text-slate-800 font-semibold">#{selectedEvent.sequence_number ?? 1}</span>
              </div>
              <div>
                <span className="text-slate-400 uppercase text-[10px] block">Event Type</span>
                <span className="text-slate-900 font-bold">{selectedEvent.event_type}</span>
              </div>
              <div>
                <span className="text-slate-400 uppercase text-[10px] block">Tenant Scope</span>
                <span className="text-slate-800">{selectedEvent.tenant_id || "Global (System)"}</span>
              </div>
              <div>
                <span className="text-slate-400 uppercase text-[10px] block">Actor</span>
                <span className="text-slate-800">{selectedEvent.actor}</span>
              </div>
              <div>
                <span className="text-slate-400 uppercase text-[10px] block">Previous Hash Link</span>
                <span className="text-slate-700 break-all">{selectedEvent.prev_hash}</span>
              </div>
              <div>
                <span className="text-slate-400 uppercase text-[10px] block">Record Canonical SHA-256</span>
                <span className="text-cyan-700 font-bold break-all">{selectedEvent.record_hash}</span>
              </div>
              <div>
                <span className="text-slate-400 uppercase text-[10px] block mb-1">Payload Details</span>
                <pre className="p-3 rounded-lg bg-slate-900 text-slate-200 text-[11px] overflow-x-auto max-h-48">
                  {JSON.stringify(selectedEvent.details, null, 2)}
                </pre>
              </div>
            </div>
            <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex justify-end">
              <Button size="sm" onClick={() => setSelectedEvent(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

