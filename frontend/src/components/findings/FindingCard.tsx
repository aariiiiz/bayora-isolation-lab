import React, { useState } from "react";
import { Finding } from "../../types";
import { Badge } from "../common/Badge";
import { EvidenceViewer } from "./EvidenceViewer";
import { ChevronDown, ChevronUp, ShieldCheck, Wrench, AlertTriangle, Info } from "lucide-react";
import { cn } from "../../lib/utils";

interface FindingCardProps {
  finding: Finding;
  defaultExpanded?: boolean;
}

export const FindingCard: React.FC<FindingCardProps> = ({ finding, defaultExpanded = false }) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 shadow-xs overflow-hidden transition-all duration-200 hover:border-slate-300">
      {/* Header clickable summary */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-5 flex items-start justify-between gap-4 cursor-pointer hover:bg-slate-50/50 transition-colors"
      >
        <div className="flex items-start gap-3.5">
          <Badge variant={finding.severity} size="sm">
            {finding.severity}
          </Badge>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-500">
                {finding.rule_id}
              </span>
              <h4 className="font-heading font-semibold text-base text-slate-900 leading-snug">
                {finding.title}
              </h4>
            </div>
            <p className="text-xs text-slate-600 mt-1 line-clamp-2 leading-relaxed">
              {finding.description}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <span className="hidden sm:inline-block text-[11px] font-mono text-slate-400 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
            {finding.detection_method}
          </span>
          <button
            type="button"
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100"
            aria-label="Toggle details"
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="px-5 pb-5 pt-1 border-t border-slate-100 space-y-4 text-xs bg-slate-50/30">
          {/* Ground-Truth Evidence */}
          <div>
            <div className="font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              <span>Extracted Vulnerability Evidence:</span>
            </div>
            <EvidenceViewer evidence={finding.evidence} />
          </div>

          {/* Remediation Guidance */}
          <div className="p-3.5 rounded-lg bg-emerald-50/80 border border-emerald-200 text-emerald-950">
            <div className="font-semibold mb-1 flex items-center gap-1.5 text-emerald-800">
              <Wrench className="w-3.5 h-3.5 text-emerald-600" />
              <span>Remediation Guidance:</span>
            </div>
            <p className="text-xs text-emerald-900 leading-relaxed font-body">
              {finding.remediation}
            </p>
          </div>

          {/* Meta & Limitations */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-200/70 text-[11px] text-slate-500">
            <div className="flex items-center gap-4">
              <span>Confidence: <strong className="text-slate-700">{finding.confidence}</strong></span>
              <span>Detection: <strong className="text-slate-700 font-mono">{finding.detection_method}</strong></span>
            </div>
            {finding.limitations && (
              <div className="flex items-center gap-1 text-slate-400 italic">
                <Info className="w-3 h-3" />
                <span>{finding.limitations}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
