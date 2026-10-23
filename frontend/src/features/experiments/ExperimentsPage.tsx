import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../services/api";
import { Experiment, Finding } from "../../types";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import { FindingCard } from "../../components/findings/FindingCard";
import { RiskMeter } from "../../components/common/RiskMeter";
import { formatBytes, formatDate } from "../../lib/utils";
import {
  FlaskConical,
  UploadCloud,
  FileCheck,
  CheckCircle2,
  AlertTriangle,
  Download,
  RotateCcw,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  Trash2,
  Cpu,
  Layers,
  ChevronRight,
  HelpCircle
} from "lucide-react";

const OPERATIONS = [
  {
    id: "isolation_access",
    title: "A. Isolation & Access-Control Review",
    badge: "Multi-Tenant",
    description: "Analyzes supplied configuration for risky access rules, missing tenant boundaries, overly broad permissions, insecure defaults, and session isolation concerns.",
    limitations: "Static evaluation of configuration rules. Runtime verification requires active harness adapters."
  },
  {
    id: "audit_integrity",
    title: "B. Audit Log Integrity Review",
    badge: "Non-Repudiation",
    description: "Validates the structure of supplied audit records, detects missing required fields, malformed timestamps, duplicate event identifiers, and broken hash-chain links.",
    limitations: "Verifies structural integrity and SHA-256 links. Does not guarantee physical host security."
  },
  {
    id: "prompt_injection",
    title: "C. Prompt-Injection & Adversarial Input Review",
    badge: "Heuristic Screening",
    description: "Inspects prompt datasets for suspicious instruction-override patterns and risky inputs. Labeled strictly as heuristic screening, not proof of runtime exploitation.",
    limitations: "Screens for known adversarial signatures and token delimiters. Novel evasion attacks may bypass static filters."
  },
  {
    id: "config_risk",
    title: "D. Configuration Risk Review",
    badge: "Hardening",
    description: "Checks supported configuration fields against explicit security rules and reports misconfigurations (hardcoded API keys, 0.0.0.0 bindings, unencrypted TLS).",
    limitations: "Validates against standard declarative configuration structures."
  }
];

export const ExperimentsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const isNew = searchParams.get("new") === "true";
  const runId = searchParams.get("runId");

  // Wizard State
  const [step, setStep] = useState<number>(1);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedOperation, setSelectedOperation] = useState<string>("isolation_access");
  const [experimentName, setExperimentName] = useState<string>("");
  const [environment, setEnvironment] = useState<string>("staging");
  const [profile, setProfile] = useState<string>("strict");
  const [description, setDescription] = useState<string>("");
  const [enableAiAdvisor, setEnableAiAdvisor] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<string>("all");

  // Fetch experiments list
  const { data: experimentsData, isLoading: loadingList } = useQuery({
    queryKey: ["experiments-list"],
    queryFn: () => api.getExperiments({ limit: 50 }),
    enabled: !isNew && !runId,
  });

  // Fetch single experiment detail if runId provided
  const { data: currentRun, isLoading: loadingDetail, refetch: refetchRun } = useQuery({
    queryKey: ["experiment-detail", runId],
    queryFn: () => api.getExperiment(runId!),
    enabled: !!runId,
  });

  // Fetch demo fixtures
  const { data: fixtures } = useQuery({
    queryKey: ["synthetic-fixtures"],
    queryFn: api.getSyntheticFixtures,
  });

  // Upload Mutation
  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) throw new Error("No file selected.");
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("name", experimentName || `Experiment-${Date.now().toString().slice(-4)}`);
      formData.append("operation", selectedOperation);
      formData.append("environment", environment);
      formData.append("profile", profile);
      formData.append("description", description);
      formData.append("enable_ai_advisor", String(enableAiAdvisor));

      return api.createExperiment(formData);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["experiments-list"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setSearchParams({ runId: data.id });
      setStep(5);
    },
  });

  // Request AI Advisory mutation
  const aiMutation = useMutation({
    mutationFn: (id: string) => api.requestAiAdvisory(id),
    onSuccess: () => {
      refetchRun();
    }
  });

  const handleLoadFixture = (fixtureKey: string) => {
    if (!fixtures || !fixtures[fixtureKey]) return;
    const fix = fixtures[fixtureKey];
    const blob = new Blob([fix.content], { type: "text/plain" });
    const file = new File([blob], fix.filename, { type: "text/plain" });
    setSelectedFile(file);
    setSelectedOperation(fix.operation);
    setExperimentName(`Audit: ${fix.filename.replace(/\.[^/.]+$/, "")}`);
  };

  const handleDownloadReport = async (id: string, name: string) => {
    try {
      const report = await api.getExperimentReport(id);
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `bayora_report_${id.slice(0, 8)}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } catch (e) {
      alert("Failed to export report: " + (e as Error).message);
    }
  };

  // If viewing a completed run
  if (runId && currentRun) {
    const findings = currentRun.findings || [];
    const filteredFindings =
      activeTab === "all"
        ? findings
        : findings.filter((f) => f.severity.toLowerCase() === activeTab.toLowerCase());

    return (
      <div className="space-y-6">
        {/* Breadcrumb Navigation & Controls */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchParams({});
                setStep(1);
              }}
            >
              ← Back to Runs
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-heading font-bold text-xl text-slate-900">
                  {currentRun.name}
                </h1>
                <Badge variant={currentRun.risk_level}>{currentRun.risk_level}</Badge>
              </div>
              <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                <span className="font-mono text-[11px] text-slate-400">ID: {currentRun.id}</span>
                <span>•</span>
                <span>{currentRun.artifact_filename} ({formatBytes(currentRun.artifact_size_bytes)})</span>
                <span>•</span>
                <span>{formatDate(currentRun.created_at)}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDownloadReport(currentRun.id, currentRun.name)}
            >
              <Download className="w-4 h-4 mr-2" />
              Download JSON Report
            </Button>
            <Button
              size="sm"
              onClick={() => {
                setSearchParams({ new: "true" });
                setStep(1);
                setSelectedFile(null);
              }}
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              New Retest
            </Button>
          </div>
        </div>

        {/* Risk Summary Bar */}
        <Card className="p-6 bg-gradient-to-br from-white to-slate-50/50">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
            <div className="md:col-span-2">
              <RiskMeter score={currentRun.risk_score} level={currentRun.risk_level} />
              <p className="text-xs text-slate-500 mt-2">
                Operation: <strong className="text-slate-700 capitalize">{currentRun.operation.replace("_", " ")}</strong> | Profile: <strong className="text-slate-700 capitalize">{currentRun.profile}</strong>
              </p>
            </div>
            <div className="md:col-span-2 grid grid-cols-4 gap-2 text-center">
              <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-100">
                <div className="text-lg font-heading font-bold text-rose-700">{currentRun.summary?.critical || 0}</div>
                <div className="text-[10px] uppercase font-semibold text-rose-600">Critical</div>
              </div>
              <div className="p-2.5 rounded-lg bg-orange-50 border border-orange-100">
                <div className="text-lg font-heading font-bold text-orange-700">{currentRun.summary?.high || 0}</div>
                <div className="text-[10px] uppercase font-semibold text-orange-600">High</div>
              </div>
              <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-100">
                <div className="text-lg font-heading font-bold text-amber-700">{currentRun.summary?.medium || 0}</div>
                <div className="text-[10px] uppercase font-semibold text-amber-600">Medium</div>
              </div>
              <div className="p-2.5 rounded-lg bg-blue-50 border border-blue-100">
                <div className="text-lg font-heading font-bold text-blue-700">{currentRun.summary?.low || 0}</div>
                <div className="text-[10px] uppercase font-semibold text-blue-600">Low</div>
              </div>
            </div>
          </div>
        </Card>

        {/* AI Threat Advisory (Groq LLaMA 3.3 integration) */}
        {currentRun.ai_analysis ? (
          <Card className="border-indigo-200 bg-gradient-to-br from-indigo-50/50 to-white">
            <CardHeader className="border-b border-indigo-100 bg-indigo-50/40">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <CardTitle className="text-indigo-950">AI Threat Advisory (Groq Fast LLM)</CardTitle>
              </div>
              <span className="text-[11px] font-mono text-indigo-600 bg-white px-2 py-0.5 rounded border border-indigo-200">
                llama-3.3-70b-versatile
              </span>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none text-slate-700 whitespace-pre-wrap font-body text-xs leading-relaxed">
                {currentRun.ai_analysis}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="flex items-center justify-between p-4 rounded-xl bg-indigo-50/60 border border-indigo-100 text-xs text-indigo-900">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span>Generate deep threat modeling and mitigation synthesis via Groq AI engine.</span>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="bg-white text-indigo-700 border-indigo-200"
              isLoading={aiMutation.isPending}
              onClick={() => aiMutation.mutate(currentRun.id)}
            >
              Analyze with AI
            </Button>
          </div>
        )}

        {/* Findings Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading font-bold text-lg text-slate-900">
              Evidence-Based Findings ({findings.length})
            </h2>

            {/* Severity Filter Tabs */}
            <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-lg text-xs">
              {["all", "critical", "high", "medium", "low"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-3 py-1 rounded-md font-medium capitalize transition-all ${
                    activeTab === tab
                      ? "bg-white text-slate-900 shadow-xs font-semibold"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          {filteredFindings.length === 0 ? (
            <Card className="p-8 text-center text-slate-500">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-800">No findings in this category</p>
              <p className="text-xs text-slate-400 mt-1">
                {activeTab === "all"
                  ? "The evaluated artifact satisfied all enforced isolation rules."
                  : `No findings matched severity level '${activeTab}'.`}
              </p>
            </Card>
          ) : (
            <div className="space-y-3">
              {filteredFindings.map((finding) => (
                <FindingCard key={finding.id} finding={finding} defaultExpanded={finding.severity === "CRITICAL"} />
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Multi-Step Workflow Wizard (Upload to Execution)
  if (isNew) {
    return (
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Wizard Header */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-4">
          <div>
            <h1 className="font-heading font-bold text-2xl text-slate-900">
              New Isolation Validation Run
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Step-by-step evidence collection and boundary verification.
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSearchParams({})}
          >
            Cancel
          </Button>
        </div>

        {/* Wizard Step Progress */}
        <div className="flex items-center justify-between text-xs">
          {[
            { num: 1, label: "Upload Artifact" },
            { num: 2, label: "Select Operation" },
            { num: 3, label: "Configure Profile" },
            { num: 4, label: "Run Analysis" },
          ].map((s, idx) => (
            <div key={s.num} className="flex items-center gap-2">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center font-bold ${
                  step === s.num
                    ? "bg-bayora-primary text-white"
                    : step > s.num
                    ? "bg-emerald-500 text-white"
                    : "bg-slate-200 text-slate-600"
                }`}
              >
                {step > s.num ? <CheckCircle2 className="w-4 h-4" /> : s.num}
              </div>
              <span className={`hidden sm:inline font-medium ${step === s.num ? "text-slate-900 font-semibold" : "text-slate-500"}`}>
                {s.label}
              </span>
              {idx < 3 && <ChevronRight className="w-4 h-4 text-slate-300 ml-2 hidden sm:block" />}
            </div>
          ))}
        </div>

        {/* STEP 1: Upload Artifact */}
        {step === 1 && (
          <div className="space-y-6">
            <Card className="p-8 border-dashed border-2 border-slate-300 hover:border-bayora-primary/60 transition-colors">
              <div className="flex flex-col items-center justify-center text-center">
                <UploadCloud className="w-12 h-12 text-bayora-primary/70 mb-3" />
                <h3 className="font-heading font-semibold text-lg text-slate-900">
                  Select Security Configuration or Test Artifact
                </h3>
                <p className="text-xs text-slate-500 mt-1 max-w-md">
                  Supported formats: <strong>JSON, JSONL, CSV, TXT, YAML</strong> (Max: 10 MB). File content is safely parsed and never executed.
                </p>

                <label className="mt-5 inline-block">
                  <input
                    type="file"
                    className="hidden"
                    accept=".json,.jsonl,.csv,.txt,.yaml,.yml"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSelectedFile(e.target.files[0]);
                        if (!experimentName) {
                          setExperimentName(`Audit: ${e.target.files[0].name.replace(/\.[^/.]+$/, "")}`);
                        }
                      }
                    }}
                  />
                  <Button type="button" size="md" className="cursor-pointer pointer-events-none">
                    Browse File from Computer
                  </Button>
                </label>
              </div>
            </Card>

            {/* Selected File Feedback */}
            {selectedFile && (
              <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileCheck className="w-6 h-6 text-blue-600" />
                  <div>
                    <div className="text-sm font-semibold text-slate-900">{selectedFile.name}</div>
                    <div className="text-xs text-slate-500">{formatBytes(selectedFile.size)} • Detected Type: {selectedFile.name.split('.').pop()?.toUpperCase()}</div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-rose-600 hover:bg-rose-50"
                  onClick={() => setSelectedFile(null)}
                >
                  <Trash2 className="w-4 h-4 mr-1" /> Remove
                </Button>
              </div>
            )}

            {/* Quick Demo Fixture Loaders for Hackathon Presentation */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="flex items-center gap-2 mb-3 text-xs font-semibold text-slate-700">
                <Sparkles className="w-4 h-4 text-amber-500" />
                <span>Instant Demo Fixtures (Click to load pre-verified sample):</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => handleLoadFixture("isolation_vulnerable")}
                  className="p-2.5 rounded-lg border border-slate-200 bg-white hover:border-bayora-primary hover:bg-blue-50/30 text-left transition-all"
                >
                  <div className="font-semibold text-slate-800">Vulnerable Multi-Tenant Policy (JSON)</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Tests wildcard tenant, shared session, and impersonation.</div>
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadFixture("audit_tampered")}
                  className="p-2.5 rounded-lg border border-slate-200 bg-white hover:border-bayora-primary hover:bg-blue-50/30 text-left transition-all"
                >
                  <div className="font-semibold text-slate-800">Tampered Audit Trail (JSON)</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Tests broken hash chains and duplicate event IDs.</div>
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadFixture("prompt_adversarial")}
                  className="p-2.5 rounded-lg border border-slate-200 bg-white hover:border-bayora-primary hover:bg-blue-50/30 text-left transition-all"
                >
                  <div className="font-semibold text-slate-800">Adversarial Prompts (JSONL)</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Tests instruction override screening and jailbreak patterns.</div>
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadFixture("config_risky")}
                  className="p-2.5 rounded-lg border border-slate-200 bg-white hover:border-bayora-primary hover:bg-blue-50/30 text-left transition-all"
                >
                  <div className="font-semibold text-slate-800">Risky Cluster Config (YAML)</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Tests hardcoded API keys and unencrypted endpoints.</div>
                </button>
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                disabled={!selectedFile}
                onClick={() => setStep(2)}
              >
                Proceed to Operation Selection <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* STEP 2: Choose Operation */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h3 className="font-heading font-semibold text-lg text-slate-900">
                Choose Security Operation
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Select the targeted security evaluation engine for this artifact.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {OPERATIONS.map((op) => (
                <div
                  key={op.id}
                  onClick={() => setSelectedOperation(op.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    selectedOperation === op.id
                      ? "border-bayora-primary bg-blue-50/40 shadow-xs ring-1 ring-bayora-primary"
                      : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-heading font-semibold text-sm text-slate-900">
                      {op.title}
                    </h4>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-semibold">
                      {op.badge}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                    {op.description}
                  </p>
                  <div className="mt-2 text-[11px] text-slate-400 italic flex items-center gap-1">
                    <HelpCircle className="w-3 h-3" />
                    <span>{op.limitations}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between pt-4">
              <Button variant="outline" onClick={() => setStep(1)}>
                ← Back
              </Button>
              <Button onClick={() => setStep(3)}>
                Configure Parameters <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* STEP 3: Configure Parameters */}
        {step === 3 && (
          <div className="space-y-6">
            <div>
              <h3 className="font-heading font-semibold text-lg text-slate-900">
                Configure Test Parameters
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Specify metadata and operational boundaries.
              </p>
            </div>

            <Card className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Experiment Name *
                </label>
                <input
                  type="text"
                  value={experimentName}
                  onChange={(e) => setExperimentName(e.target.value)}
                  placeholder="e.g. Cluster Tenant Scoping Review"
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-bayora-primary/20 focus:outline-hidden"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Environment Label
                  </label>
                  <select
                    value={environment}
                    onChange={(e) => setEnvironment(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs bg-white"
                  >
                    <option value="staging">Staging</option>
                    <option value="production">Production</option>
                    <option value="sandbox-eval">Sandbox Evaluation</option>
                    <option value="red-team-drill">Red-Team Drill</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Validation Profile
                  </label>
                  <select
                    value={profile}
                    onChange={(e) => setProfile(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs bg-white"
                  >
                    <option value="strict">Strict (Zero tolerance for wildcards)</option>
                    <option value="standard">Standard (Baseline enterprise RBAC)</option>
                    <option value="permissive">Permissive (Exploratory / warning only)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Optional Description / Context
                </label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Notes regarding the test harness or deployment architecture..."
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-bayora-primary/20 focus:outline-hidden"
                />
              </div>

              {/* AI Advisor Toggle (Groq) */}
              <div className="pt-3 border-t border-slate-200">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={enableAiAdvisor}
                    onChange={(e) => setEnableAiAdvisor(e.target.checked)}
                    className="w-4 h-4 rounded text-bayora-primary focus:ring-bayora-primary"
                  />
                  <div>
                    <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                      Enable Groq AI Threat Advisory & Mitigation Synthesis
                    </span>
                    <span className="text-[11px] text-slate-500 block">
                      Synthesizes attacker STRIDE threat modeling and targeted architectural patches.
                    </span>
                  </div>
                </label>
              </div>
            </Card>

            <div className="flex items-center justify-between pt-4">
              <Button variant="outline" onClick={() => setStep(2)}>
                ← Back
              </Button>
              <Button
                isLoading={uploadMutation.isPending}
                onClick={() => {
                  setStep(4);
                  uploadMutation.mutate();
                }}
              >
                Execute Validation Engine <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* STEP 4: Execution Progress */}
        {step === 4 && (
          <Card className="p-12 text-center">
            <Cpu className="w-12 h-12 text-bayora-primary animate-pulse mx-auto mb-4" />
            <h3 className="font-heading font-semibold text-lg text-slate-900">
              Executing Deterministic Analysis Engine...
            </h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Safely parsing artifact, evaluating active isolation rules, checking boundary integrity, and computing cryptographic hash signatures.
            </p>
            {uploadMutation.isError && (
              <div className="mt-4 p-3 rounded-lg bg-rose-50 text-rose-700 text-xs">
                {(uploadMutation.error as Error).message}
              </div>
            )}
          </Card>
        )}
      </div>
    );
  }

  // DEFAULT VIEW: Experiments List
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl text-slate-900">
            Experiment Runs
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Historical evaluations, ground-truth evidence records, and residual-risk profiles.
          </p>
        </div>
        <Button onClick={() => setSearchParams({ new: "true" })}>
          <FlaskConical className="w-4 h-4 mr-2" />
          New Validation Run
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Validation History ({experimentsData?.total || 0})</CardTitle>
        </CardHeader>
        <div className="divide-y divide-slate-100">
          {loadingList ? (
            <div className="p-8 text-center text-xs text-slate-500">Loading experiments...</div>
          ) : !experimentsData?.items || experimentsData.items.length === 0 ? (
            <div className="p-12 text-center">
              <FlaskConical className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-700">No experiments found</p>
              <p className="text-xs text-slate-400 mt-1">
                Upload a test artifact to run your first isolation validation.
              </p>
              <Button
                size="sm"
                className="mt-4"
                onClick={() => setSearchParams({ new: "true" })}
              >
                Launch First Run
              </Button>
            </div>
          ) : (
            experimentsData.items.map((exp) => (
              <div
                key={exp.id}
                className="p-5 flex flex-wrap items-center justify-between gap-4 hover:bg-slate-50/60 transition-colors"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2.5">
                    <span className="font-heading font-semibold text-sm text-slate-900">
                      {exp.name}
                    </span>
                    <Badge variant={exp.risk_level} size="sm">
                      {exp.risk_level}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-1">
                    <span className="font-medium text-slate-700 capitalize">
                      {exp.operation.replace("_", " ")}
                    </span>
                    <span>•</span>
                    <span className="font-mono text-[11px]">{exp.artifact_filename}</span>
                    <span>•</span>
                    <span>Risk: <strong>{exp.risk_score.toFixed(0)}/100</strong></span>
                    <span>•</span>
                    <span>{formatDate(exp.created_at)}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDownloadReport(exp.id, exp.name)}
                    title="Export JSON report"
                  >
                    <Download className="w-3.5 h-3.5 mr-1" /> JSON
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => setSearchParams({ runId: exp.id })}
                  >
                    View Details
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};
