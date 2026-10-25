import React, { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
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
  Check
} from "lucide-react";

export const AuditTrailPage: React.FC = () => {
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [verificationResult, setVerificationResult] = useState<AuditVerificationReport | null>(null);

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
            Sequential non-repudiation ledger bound by cryptographic SHA-256 hash chaining.
          </p>
        </div>

        <Button
          onClick={() => verifyMutation.mutate()}
          isLoading={verifyMutation.isPending}
          className="bg-slate-900 hover:bg-slate-800 text-white"
        >
          <ShieldCheck className="w-4 h-4 mr-2 text-cyan-400" />
          Verify Cryptographic Chain Integrity
        </Button>
      </div>

      {/* Verification Result Banner */}
      {verificationResult && (
        <div
          className={`p-4 rounded-xl border flex items-start justify-between gap-3 ${
            verificationResult.valid
              ? "bg-emerald-50 border-emerald-200 text-emerald-950"
              : "bg-rose-50 border-rose-200 text-rose-950"
          }`}
        >
          <div className="flex items-start gap-3">
            {verificationResult.valid ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <AlertOctagon className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            )}
            <div>
              <div className="font-heading font-bold text-sm">
                {verificationResult.valid
                  ? "Cryptographic Chain Integrity Verified (Zero Tampering Detected)"
                  : "Cryptographic Chain Break Detected!"}
              </div>
              <p className="text-xs mt-0.5 opacity-90">{verificationResult.message}</p>
              {verificationResult.latest_hash && (
                <div className="mt-1 font-mono text-[10px] opacity-80 flex flex-wrap gap-4">
                  <span>Sequence Check: #{verificationResult.latest_sequence ?? verificationResult.total_verified}</span>
                  <span>Checkpoint Status: {verificationResult.checkpoint_status?.verified ? "Verified against external anchor" : "Local chain valid"}</span>
                  <span className="truncate max-w-xs">Hash: {verificationResult.latest_hash}</span>
                </div>
              )}
            </div>
          </div>
          <button
            onClick={() => setVerificationResult(null)}
            className="text-xs opacity-60 hover:opacity-100 font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

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
                events.map((evt) => (
                  <tr key={evt.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-[11px] text-slate-500">
                      #{evt.sequence_number ?? 1}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-900 font-mono text-[11px]">
                      <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                        {evt.event_type}
                      </span>
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
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

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
                <span className="text-slate-400 uppercase text-[10px] block">Event Type</span>
                <span className="text-slate-900 font-bold">{selectedEvent.event_type}</span>
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
