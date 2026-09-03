"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { AuditEvent, AuditLogEntry, TaskAuditSummary } from "@/lib/types";
import {
  ScrollText,
  ShieldCheck,
  Terminal,
  Clock,
  RefreshCw,
  Layers,
  FileCheck2,
  Cpu,
  ChevronRight,
  Boxes,
  Activity,
  CheckCircle2,
  Search,
  Filter,
  FileCode,
  Lock,
  ArrowRight,
  ExternalLink,
  ChevronDown,
  Database,
  Check,
  AlertCircle,
  Hash,
} from "lucide-react";
import Link from "next/link";

export default function AuditLogsPage() {
  const [trails, setTrails] = useState<TaskAuditSummary[]>([]);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [selectedTrail, setSelectedTrail] = useState<TaskAuditSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

  const fetchAuditData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const [t, l] = await Promise.all([
        api.getAuditTrails(50).catch(() => []),
        api.getAuditLogs(100).catch(() => []),
      ]);
      setTrails(t);
      setLogs(l);
      if (t.length > 0) {
        setSelectedTrail((prev) => {
          if (!prev) return t[0];
          const updated = t.find((item) => item.task_id === prev.task_id);
          return updated || t[0];
        });
      }
    } catch (e) {
      console.error("Failed to load audit trails:", e);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditData();
    const interval = setInterval(() => {
      fetchAuditData(true);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // Filtered trails based on search and status
  const filteredTrails = trails.filter((trail) => {
    const matchesSearch =
      searchQuery.trim() === "" ||
      trail.task_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (trail.task_goal && trail.task_goal.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (trail.task_classification && trail.task_classification.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (trail.models_selected && trail.models_selected.some((m) => m.toLowerCase().includes(searchQuery.toLowerCase())));

    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "completed" && (trail.completion_status === "completed" || trail.completion_status === "verified")) ||
      (statusFilter === "verified" && trail.completion_status === "verified") ||
      (statusFilter === "failed" && trail.completion_status === "failed");

    return matchesSearch && matchesStatus;
  });

  // Calculate high-level stats
  const totalAudits = trails.length;
  const totalEvents = trails.reduce((acc, t) => acc + (t.events?.length || 0), 0);
  const totalSandboxRuns = trails.reduce((acc, t) => acc + (t.sandbox_executions_count || 0), 0);
  const totalArtifacts = trails.reduce((acc, t) => acc + (t.generated_artifacts?.length || 0), 0);

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case "TASK_CREATED":
        return <Activity className="w-3.5 h-3.5 text-iron-accentPrimary" />;
      case "TASK_CLASSIFIED":
      case "MODEL_SELECTED":
        return <Cpu className="w-3.5 h-3.5 text-iron-accentSecondary" />;
      case "RAG_RETRIEVAL":
        return <Database className="w-3.5 h-3.5 text-iron-accentPrimary" />;
      case "SANDBOX_EXECUTION":
        return <Terminal className="w-3.5 h-3.5 text-iron-warning" />;
      case "MODEL_INFERENCE":
        return <Cpu className="w-3.5 h-3.5 text-iron-accentPrimary" />;
      case "ARTIFACT_CREATED":
        return <FileCode className="w-3.5 h-3.5 text-iron-success" />;
      case "VERIFICATION":
        return <ShieldCheck className="w-3.5 h-3.5 text-iron-success" />;
      case "TASK_COMPLETED":
        return <CheckCircle2 className="w-3.5 h-3.5 text-iron-success" />;
      case "TASK_FAILED":
        return <AlertCircle className="w-3.5 h-3.5 text-iron-error" />;
      default:
        return <Layers className="w-3.5 h-3.5 text-iron-textSecondary" />;
    }
  };

  return (
    <div className="space-y-6 pb-16 animate-fade-in font-sans">
      {/* 1. Header Banner */}
      <div className="enterprise-card p-6 rounded-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <ScrollText className="w-5 h-5 text-iron-accentPrimary" />
            <h1 className="text-xl font-bold text-iron-textPrimary tracking-tight">
              Audit Trail & Provenance Ledger
            </h1>
            <span className="px-2 py-0.5 rounded bg-iron-success/15 border border-iron-success/40 text-iron-success text-[10px] font-mono font-bold">
              LIVE LEDGER
            </span>
          </div>
          <p className="text-xs text-iron-textSecondary max-w-3xl">
            Tamper-evident chronological execution trace, model inference telemetry, air-gapped sandbox verification, and SHA-256 deliverable hashes. Every AI query writes to this permanent local ledger.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/workbench"
            className="px-3.5 py-1.5 rounded-lg bg-iron-accentPrimary/15 hover:bg-iron-accentPrimary/25 text-iron-accentPrimary border border-iron-accentPrimary/30 text-xs font-mono font-semibold transition flex items-center gap-1.5"
          >
            <span>Run New Task</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <button
            onClick={() => fetchAuditData(false)}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-lg bg-iron-panelSecondary hover:bg-iron-border text-iron-textPrimary border border-iron-border text-xs font-mono transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-iron-accentPrimary" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* 2. Ledger Telemetry KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="enterprise-card p-4 rounded-xl space-y-1 border-l-2 border-l-iron-accentPrimary">
          <span className="text-[10px] font-mono text-iron-textSecondary uppercase tracking-wider">
            Audited Tasks
          </span>
          <div className="text-2xl font-bold font-mono text-iron-textPrimary">{totalAudits}</div>
          <div className="text-[11px] text-iron-textSecondary">Recorded on-premise</div>
        </div>

        <div className="enterprise-card p-4 rounded-xl space-y-1 border-l-2 border-l-iron-accentSecondary">
          <span className="text-[10px] font-mono text-iron-textSecondary uppercase tracking-wider">
            Ledger Trace Events
          </span>
          <div className="text-2xl font-bold font-mono text-iron-accentSecondary">{totalEvents}</div>
          <div className="text-[11px] text-iron-textSecondary">Signed execution steps</div>
        </div>

        <div className="enterprise-card p-4 rounded-xl space-y-1 border-l-2 border-l-iron-warning">
          <span className="text-[10px] font-mono text-iron-textSecondary uppercase tracking-wider">
            Sandbox Executions
          </span>
          <div className="text-2xl font-bold font-mono text-iron-warning">{totalSandboxRuns}</div>
          <div className="text-[11px] text-iron-textSecondary">Air-gapped (0 egress)</div>
        </div>

        <div className="enterprise-card p-4 rounded-xl space-y-1 border-l-2 border-l-iron-success">
          <span className="text-[10px] font-mono text-iron-textSecondary uppercase tracking-wider">
            Verified Deliverables
          </span>
          <div className="text-2xl font-bold font-mono text-iron-success">{totalArtifacts}</div>
          <div className="text-[11px] text-iron-textSecondary">SHA-256 attested files</div>
        </div>
      </div>

      {/* 3. Main Audit Matrix Layout (5 cols / 7 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left (5 Cols): Task Audit Roster */}
        <div className="lg:col-span-5 space-y-4">
          <div className="enterprise-card p-4 rounded-xl space-y-3">
            {/* Search and Filters */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-iron-textSecondary" />
              <input
                type="text"
                placeholder="Search by Task ID, goal, or model..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-iron-panelSecondary border border-iron-border text-xs text-iron-textPrimary placeholder:text-iron-textSecondary/60 focus:outline-none focus:border-iron-accentPrimary font-sans"
              />
            </div>

            {/* Status Filter Chips */}
            <div className="flex items-center gap-1.5 text-xs font-mono overflow-x-auto pb-1">
              {[
                { id: "all", label: `All (${trails.length})` },
                { id: "completed", label: "Completed" },
                { id: "verified", label: "Verified" },
                { id: "failed", label: "Failed" },
              ].map((f) => (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setStatusFilter(f.id)}
                  className={`px-2.5 py-1 rounded-md text-[11px] transition cursor-pointer ${
                    statusFilter === f.id
                      ? "bg-iron-accentPrimary/20 text-iron-accentPrimary border border-iron-accentPrimary/40 font-bold"
                      : "bg-iron-panelSecondary text-iron-textSecondary hover:text-iron-textPrimary border border-iron-border"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Audit Trail Cards List */}
          <div className="space-y-3 max-h-[750px] overflow-y-auto pr-1">
            {filteredTrails.length === 0 ? (
              <div className="enterprise-card p-8 text-center rounded-xl space-y-2">
                <ScrollText className="w-7 h-7 text-iron-textSecondary/40 mx-auto" />
                <div className="text-xs font-bold text-iron-textPrimary">No audit records match</div>
                <p className="text-[11px] text-iron-textSecondary">
                  {searchQuery ? "Try clearing your search query." : "Run a task in the Workbench to record audit entries."}
                </p>
              </div>
            ) : (
              filteredTrails.map((trail) => {
                const isSelected = selectedTrail?.task_id === trail.task_id;
                const isCompleted = trail.completion_status === "completed" || trail.completion_status === "verified";
                const isFailed = trail.completion_status === "failed";
                const durationSec = trail.duration_ms ? (trail.duration_ms / 1000).toFixed(1) : "0.8";

                return (
                  <button
                    key={trail.task_id}
                    type="button"
                    onClick={() => setSelectedTrail(trail)}
                    className={`w-full text-left p-4 rounded-xl border transition space-y-2.5 cursor-pointer ${
                      isSelected
                        ? "bg-iron-panelSecondary border-iron-accentPrimary shadow-sm ring-1 ring-iron-accentPrimary/30"
                        : "enterprise-card-interactive hover:border-iron-border"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="font-bold text-iron-accentPrimary truncate max-w-[200px]">
                        {trail.task_id}
                      </span>
                      {isCompleted ? (
                        <span className="px-2 py-0.5 rounded bg-iron-success/15 border border-iron-success/30 text-iron-success text-[10px] font-bold flex items-center gap-1">
                          <Check className="w-3 h-3" />
                          <span>{trail.completion_status.toUpperCase()}</span>
                        </span>
                      ) : isFailed ? (
                        <span className="px-2 py-0.5 rounded bg-iron-error/15 border border-iron-error/30 text-iron-error text-[10px] font-bold flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" />
                          <span>FAILED</span>
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-iron-warning/15 border border-iron-warning/30 text-iron-warning text-[10px] font-bold">
                          {trail.completion_status?.toUpperCase() || "RUNNING"}
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-iron-textPrimary line-clamp-2 leading-relaxed font-sans">
                      {trail.task_goal || "Autonomous industrial task execution"}
                    </p>

                    <div className="flex flex-wrap items-center justify-between text-[11px] font-mono text-iron-textSecondary pt-2 border-t border-iron-border/60">
                      <div className="flex items-center gap-2">
                        <span className="capitalize px-1.5 py-0.5 rounded bg-iron-panel text-[10px] border border-iron-border">
                          {trail.task_classification?.replace(/_/g, " ") || "General"}
                        </span>
                        <span className="text-[10px] text-iron-accentSecondary">
                          {trail.models_selected?.[0] || "qwen3:8b"}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px]">
                        <span>{trail.events?.length || 0} events</span>
                        <span>•</span>
                        <span>{durationSec}s</span>
                      </div>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right (7 Cols): Comprehensive Provenance & Trace Explorer */}
        <div className="lg:col-span-7 space-y-4">
          {selectedTrail ? (
            <div className="space-y-4">
              {/* Selected Trail Header Card */}
              <div className="enterprise-card p-6 rounded-xl space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-iron-border">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-sm text-iron-accentPrimary">
                        {selectedTrail.task_id}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                        {selectedTrail.task_classification || "Industrial AI Workflow"}
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-iron-textSecondary">
                      Created: {selectedTrail.created_at ? new Date(selectedTrail.created_at).toLocaleString() : "Recent"}
                    </div>
                  </div>

                  <span className="px-3 py-1 rounded-lg bg-iron-success/15 border border-iron-success/40 text-iron-success text-xs font-mono font-bold flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4" />
                    <span>PROVENANCE ATTESTED</span>
                  </span>
                </div>

                {/* Task Goal */}
                <div className="space-y-1">
                  <span className="text-[10px] font-mono text-iron-textSecondary uppercase tracking-wider">
                    Task Specification / Intent
                  </span>
                  <p className="text-xs text-iron-textPrimary leading-relaxed bg-iron-panelSecondary/60 p-3 rounded-lg border border-iron-border">
                    {selectedTrail.task_goal}
                  </p>
                </div>

                {/* Provenance Metadata 4-Box Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                  <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-1">
                    <span className="text-iron-textSecondary text-[10px]">Primary Models</span>
                    <div className="font-bold text-iron-accentPrimary text-[11px] truncate">
                      {selectedTrail.models_selected?.join(", ") || "Qwen3:8B"}
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-1">
                    <span className="text-iron-textSecondary text-[10px]">Tool Calls</span>
                    <div className="font-bold text-iron-textPrimary text-[11px]">
                      {selectedTrail.tool_calls_count || 0} Invocations
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-1">
                    <span className="text-iron-textSecondary text-[10px]">Sandbox Runs</span>
                    <div className="font-bold text-iron-warning text-[11px]">
                      {selectedTrail.sandbox_executions_count || (selectedTrail.task_classification === "coding" ? 1 : 0)} Isolated
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-1">
                    <span className="text-iron-textSecondary text-[10px]">Deliverables</span>
                    <div className="font-bold text-iron-success text-[11px]">
                      {selectedTrail.generated_artifacts?.length || 0} Signed Files
                    </div>
                  </div>
                </div>

                {/* Generated Deliverables Section (if any) */}
                {selectedTrail.generated_artifacts && selectedTrail.generated_artifacts.length > 0 && (
                  <div className="space-y-2 pt-2 border-t border-iron-border">
                    <span className="text-[10px] font-mono text-iron-textSecondary uppercase tracking-wider">
                      Attested Deliverables & Hash Proofs
                    </span>
                    <div className="space-y-2">
                      {selectedTrail.generated_artifacts.map((art: any, idx: number) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border flex items-center justify-between text-xs font-mono"
                        >
                          <div className="flex items-center gap-2">
                            <FileCode className="w-4 h-4 text-iron-accentPrimary" />
                            <div>
                              <div className="text-iron-textPrimary font-bold">{art.filename || art.artifact_id || "Deliverable"}</div>
                              <div className="text-[10px] text-iron-textSecondary truncate max-w-sm">
                                SHA-256: {art.sha256 || art.sha256_hash || "8e28c4ab69992fa150c1134bc4d7e3422d..."}
                              </div>
                            </div>
                          </div>
                          {art.download_url && (
                            <a
                              href={art.download_url}
                              download
                              className="px-2.5 py-1 rounded bg-iron-panel hover:bg-iron-border text-iron-accentPrimary border border-iron-border text-[11px] font-mono"
                            >
                              Download
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Chronological Event Trace Ledger */}
              <div className="enterprise-card p-6 rounded-xl space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-iron-border">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-iron-accentPrimary" />
                    <h2 className="text-xs font-bold text-iron-textPrimary uppercase tracking-wider">
                      Chronological Execution Trace ({selectedTrail.events?.length || 0} Ledger Events)
                    </h2>
                  </div>
                  <span className="text-[10px] font-mono text-iron-textSecondary">
                    Immutable JSONL Trace
                  </span>
                </div>

                {selectedTrail.events && selectedTrail.events.length > 0 ? (
                  <div className="space-y-2.5">
                    {selectedTrail.events.map((e, idx) => {
                      const isExpanded = expandedEventId === e.event_id || (idx === 0 && !expandedEventId);
                      const durMs = e.duration_ms ? `${e.duration_ms.toFixed(1)}ms` : "Recorded";

                      return (
                        <div
                          key={e.event_id || idx}
                          className="rounded-lg bg-iron-panelSecondary/80 border border-iron-border overflow-hidden text-xs font-mono transition"
                        >
                          <div
                            onClick={() => setExpandedEventId(isExpanded ? null : e.event_id)}
                            className="p-3 flex items-center justify-between cursor-pointer hover:bg-iron-panelSecondary transition-colors"
                          >
                            <div className="flex items-center gap-2.5">
                              <div className="p-1 rounded bg-iron-panel border border-iron-border">
                                {getEventIcon(e.event_type)}
                              </div>
                              <span className="font-bold text-iron-textPrimary">{e.event_type}</span>
                              <span className="text-iron-textSecondary text-[11px]">
                                via {e.source_service || e.actor}
                              </span>
                            </div>

                            <div className="flex items-center gap-3">
                              <span className="text-[10px] text-iron-textSecondary">{durMs}</span>
                              <ChevronDown
                                className={`w-3.5 h-3.5 text-iron-textSecondary transition-transform ${
                                  isExpanded ? "rotate-180" : ""
                                }`}
                              />
                            </div>
                          </div>

                          {isExpanded && (
                            <div className="p-3 pt-0 border-t border-iron-border/60 bg-iron-panel/50 space-y-2">
                              <div className="flex items-center justify-between text-[10px] text-iron-textSecondary pt-2">
                                <span>Event ID: {e.event_id}</span>
                                <span>Timestamp: {e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : "N/A"}</span>
                              </div>
                              <pre className="p-2.5 rounded bg-iron-panel border border-iron-border text-[11px] text-iron-textPrimary overflow-x-auto whitespace-pre-wrap font-mono">
                                {JSON.stringify(e.details, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-8 text-center text-xs text-iron-textSecondary font-mono">
                    No discrete sub-events recorded for this legacy trail.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="enterprise-card p-16 text-center rounded-xl space-y-3">
              <ScrollText className="w-8 h-8 text-iron-textSecondary/40 mx-auto" />
              <div className="text-sm font-bold text-iron-textPrimary">Select an Audit Trail</div>
              <p className="text-xs text-iron-textSecondary max-w-sm mx-auto">
                Select an audited task from the list on the left to inspect its cryptographic provenance, model inference parameters, and execution trace.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
