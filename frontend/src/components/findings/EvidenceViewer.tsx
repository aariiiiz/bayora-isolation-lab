import React from "react";
import { Terminal, Copy, Check } from "lucide-react";

interface EvidenceViewerProps {
  evidence: Record<string, any>;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({ evidence }) => {
  const [copied, setCopied] = React.useState(false);

  const formattedJson = JSON.stringify(evidence, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(formattedJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden bg-slate-900 text-slate-100 text-xs font-mono">
      <div className="bg-slate-950 px-3 py-2 flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center gap-2 text-slate-400">
          <Terminal className="w-3.5 h-3.5" />
          <span>Artifact Ground-Truth Evidence</span>
          {evidence.line_number && (
            <span className="bg-slate-800 px-1.5 py-0.5 rounded text-[10px] text-cyan-400">
              Line {evidence.line_number}
            </span>
          )}
        </div>
        <button
          onClick={handleCopy}
          className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition-colors"
          title="Copy evidence payload"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
        </button>
      </div>

      <div className="p-3.5 overflow-x-auto max-h-56">
        {evidence.excerpt && (
          <div className="mb-2 p-2 bg-slate-950/80 rounded border-l-2 border-cyan-400 text-slate-200">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5 font-bold">
              Matched Excerpt:
            </div>
            <code>{evidence.excerpt}</code>
          </div>
        )}
        <pre className="text-slate-300 text-[11px] leading-relaxed">{formattedJson}</pre>
      </div>
    </div>
  );
};
