import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../services/api";
import { Policy, Severity } from "../../types";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { Badge } from "../../components/common/Badge";
import {
  Sliders,
  Plus,
  ShieldCheck,
  ToggleLeft,
  ToggleRight,
  Trash2,
  Edit2,
  Check,
  AlertTriangle,
  Info,
  Shield
} from "lucide-react";

export const PoliciesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<Policy | null>(null);

  // Form State
  const [ruleId, setRuleId] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState<"isolation" | "audit" | "prompt" | "config">("isolation");
  const [severity, setSeverity] = useState<Severity>("HIGH");
  const [description, setDescription] = useState("");
  const [explanation, setExplanation] = useState("");
  const [remediation, setRemediation] = useState("");

  const { data: policies = [], isLoading } = useQuery({
    queryKey: ["policies-list", selectedCategory],
    queryFn: () => api.getPolicies(selectedCategory === "all" ? {} : { category: selectedCategory }),
  });

  // Toggle Mutation
  const toggleMutation = useMutation({
    mutationFn: ({ id, is_enabled }: { id: string; is_enabled: boolean }) =>
      api.updatePolicy(id, { is_enabled }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["policies-list"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deletePolicy(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["policies-list"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
    onError: (err: Error) => {
      alert(err.message);
    },
  });

  // Create Policy Mutation
  const createMutation = useMutation({
    mutationFn: api.createPolicy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["policies-list"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setIsModalOpen(false);
      resetForm();
    },
    onError: (err: Error) => {
      alert("Failed to create policy: " + err.message);
    },
  });

  const resetForm = () => {
    setRuleId("");
    setName("");
    setCategory("isolation");
    setSeverity("HIGH");
    setDescription("");
    setExplanation("");
    setRemediation("");
    setEditingPolicy(null);
  };

  const handleOpenCreate = () => {
    resetForm();
    setIsModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ruleId || !name || !description || !explanation || !remediation) {
      alert("Please fill in all required fields.");
      return;
    }
    createMutation.mutate({
      rule_id: ruleId.trim().toUpperCase(),
      name,
      category,
      severity,
      is_enabled: true,
      description,
      explanation,
      remediation,
      parameters: {},
      is_baseline: false,
    });
  };

  return (
    <div className="space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl text-slate-900">
            Isolation & Security Policies
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Declarative safety rules enforced during boundary inspections and adversarial drills.
          </p>
        </div>

        <Button onClick={handleOpenCreate}>
          <Plus className="w-4 h-4 mr-2" />
          Create Custom Rule
        </Button>
      </div>

      {/* Category Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3 text-xs">
        {[
          { id: "all", label: "All Rules" },
          { id: "isolation", label: "Tenant & Session Isolation" },
          { id: "audit", label: "Audit Integrity" },
          { id: "prompt", label: "Prompt Security" },
          { id: "config", label: "Configuration Risk" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedCategory(tab.id)}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              selectedCategory === tab.id
                ? "bg-bayora-sidebarActive text-bayora-primary font-bold shadow-2xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Policies List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading security policies...</div>
        ) : policies.length === 0 ? (
          <Card className="p-10 text-center text-slate-500">
            <Sliders className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-800">No policies in this category</p>
          </Card>
        ) : (
          policies.map((p) => (
            <Card key={p.id} className="p-5 hover:border-slate-300 transition-all">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="flex items-start gap-3.5">
                  <Badge variant={p.severity} size="sm">
                    {p.severity}
                  </Badge>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                        {p.rule_id}
                      </span>
                      <h3 className="font-heading font-semibold text-sm text-slate-900">
                        {p.name}
                      </h3>
                      {p.is_baseline && (
                        <span className="text-[10px] font-mono text-cyan-700 bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200 font-semibold">
                          Baseline Rule
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                      {p.description}
                    </p>
                    <div className="mt-3 p-3 rounded-lg bg-slate-50 border border-slate-100 text-[11px] space-y-1">
                      <div>
                        <strong className="text-slate-700">Threat Explanation:</strong> {p.explanation}
                      </div>
                      <div>
                        <strong className="text-emerald-700">Remediation:</strong> {p.remediation}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {/* Enable / Disable Toggle */}
                  <button
                    onClick={() => toggleMutation.mutate({ id: p.id, is_enabled: !p.is_enabled })}
                    className="flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900"
                    title={p.is_enabled ? "Disable this rule" : "Enable this rule"}
                  >
                    {p.is_enabled ? (
                      <ToggleRight className="w-6 h-6 text-emerald-600" />
                    ) : (
                      <ToggleLeft className="w-6 h-6 text-slate-400" />
                    )}
                    <span className={p.is_enabled ? "text-emerald-700 font-bold" : "text-slate-400"}>
                      {p.is_enabled ? "Active" : "Disabled"}
                    </span>
                  </button>

                  {/* Delete (if not baseline) */}
                  {!p.is_baseline && (
                    <button
                      onClick={() => {
                        if (confirm(`Are you sure you want to delete policy ${p.rule_id}?`)) {
                          deleteMutation.mutate(p.id);
                        }
                      }}
                      className="p-1.5 rounded text-rose-500 hover:bg-rose-50 hover:text-rose-700"
                      title="Delete custom rule"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Create Custom Rule Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-heading font-semibold text-base text-slate-900">
                Create Custom Isolation Rule
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Rule ID (e.g. CUST-001) *
                  </label>
                  <input
                    type="text"
                    required
                    value={ruleId}
                    onChange={(e) => setRuleId(e.target.value)}
                    placeholder="ISO-CUSTOM-01"
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Category *</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white"
                  >
                    <option value="isolation">Tenant & Session Isolation</option>
                    <option value="audit">Audit Integrity</option>
                    <option value="prompt">Prompt Security</option>
                    <option value="config">Configuration Risk</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Rule Title *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Mandatory Network Egress Scoping"
                  className="w-full px-3 py-2 rounded-lg border border-slate-300"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Severity *</label>
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value as Severity)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white"
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                  <option value="INFO">INFO</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description *</label>
                <textarea
                  rows={2}
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What this rule validates..."
                  className="w-full px-3 py-2 rounded-lg border border-slate-300"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Threat Explanation *
                </label>
                <textarea
                  rows={2}
                  required
                  value={explanation}
                  onChange={(e) => setExplanation(e.target.value)}
                  placeholder="Why violating this rule is dangerous..."
                  className="w-full px-3 py-2 rounded-lg border border-slate-300"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Remediation Guidance *
                </label>
                <textarea
                  rows={2}
                  required
                  value={remediation}
                  onChange={(e) => setRemediation(e.target.value)}
                  placeholder="How developers should fix this violation..."
                  className="w-full px-3 py-2 rounded-lg border border-slate-300"
                />
              </div>

              <div className="pt-3 border-t border-slate-100 flex justify-end gap-2">
                <Button variant="outline" type="button" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={createMutation.isPending}>
                  Save Policy
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
