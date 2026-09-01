"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { AuditLogEntry, TaskAuditSummary } from "@/lib/types";
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
} from "lucide-react";

export default function AuditLogsPage() {
  const [trails, setTrails] = useState<TaskAuditSummary[]>([]);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [selectedTrail, setSelectedTrail] = useState<TaskAuditSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAuditData = async () => {
    try {
      setLoading(true);
      const [t, l] = await Promise.all([
        api.getAuditTrails(50).catch(() => []),
        api.getAuditLogs(100).catch(() => []),
      ]);
      setTrails(t);
      setLogs(l);
      if (t.length > 0 && !selectedTrail) {
        setSelectedTrail(t[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, []);

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-3xl glass-panel relative overflow-hidden">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <ScrollText className="w-6 h-6 text-indigo-400" />
            <span>Audit Trail & Provenance Ledger</span>
          </h2>
          <p className="text-xs md:text-sm text-slate-400">
            Immutable chronological execution trace, model inference parameters, and cryptographic verification logs.
          </p>
        </div>
        <button
          onClick={fetchAuditData}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.09] text-slate-200 text-xs font-semibold transition border border-white/10"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
          <span>Refresh Ledger</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Task Provenance Cards (5 Cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-400 px-1">
            <span>AUDIT TRAILS ({trails.length})</span>
          </div>

          {trails.length === 0 ? (
            <div className="p-12 text-center rounded-3xl glass-panel space-y-3">
              <ScrollText className="w-8 h-8 text-slate-600 mx-auto" />
              <div className="text-sm font-semibold text-slate-300">No audit trails recorded yet</div>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                All future tasks executed in the workbench will appear here with cryptographic hashes.
              </p>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[680px] overflow-y-auto pr-1">
              {trails.map((trail) => {
                const isSelected = selectedTrail?.task_id === trail.task_id;
                return (
                  <button
                    key={trail.task_id}
                    type="button"
                    onClick={() => setSelectedTrail(trail)}
                    className={`w-full text-left p-4 rounded-2xl border transition space-y-2 cursor-pointer ${
                      isSelected
                        ? "bg-indigo-500/10 border-indigo-500/40 shadow-lg shadow-indigo-500/15"
                        : "glass-panel-interactive border-white/5"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="font-bold text-indigo-400">{trail.task_id}</span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 uppercase">
                        {trail.completion_status}
                      </span>
                    </div>

                    <p className="text-xs text-slate-200 line-clamp-2 leading-relaxed">
                      {trail.task_goal}
                    </p>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-white/5 font-mono">
                      <span>{trail.task_classification || "Autonomous Workflow"}</span>
                      <span>{trail.duration_ms ? `${(trail.duration_ms / 1000).toFixed(1)}s` : "Recorded"}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Audit Details & Ledger (7 Cols) */}
        <div className="lg:col-span-7 space-y-5">
          {selectedTrail ? (
            <div className="space-y-5">
              {/* Summary Card */}
              <div className="p-6 rounded-3xl glass-panel space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-indigo-400 font-bold">
                    {selectedTrail.task_id}
                  </span>
                  <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                    Provenance Verified
                  </span>
                </div>

                <h3 className="text-base font-bold text-white leading-snug">{selectedTrail.task_goal}</h3>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-white/5 text-xs">
                  <div className="p-3 rounded-xl bg-obsidian-950/80 border border-white/5 space-y-1">
                    <span className="text-slate-500 text-[10px]">Classification</span>
                    <div className="font-mono text-slate-200 text-[11px] truncate">{selectedTrail.task_classification || "General"}</div>
                  </div>
                  <div className="p-3 rounded-xl bg-obsidian-950/80 border border-white/5 space-y-1">
                    <span className="text-slate-500 text-[10px]">Models</span>
                    <div className="font-mono text-indigo-400 text-[11px] font-bold truncate">{selectedTrail.models_selected?.join(", ") || "Multi-Stage"}</div>
                  </div>
                  <div className="p-3 rounded-xl bg-obsidian-950/80 border border-white/5 space-y-1">
                    <span className="text-slate-500 text-[10px]">Tools</span>
                    <div className="font-mono text-slate-200 text-[11px]">{selectedTrail.tool_calls_count || 0} Calls</div>
                  </div>
                  <div className="p-3 rounded-xl bg-obsidian-950/80 border border-white/5 space-y-1">
                    <span className="text-slate-500 text-[10px]">Deliverables</span>
                    <div className="font-mono text-emerald-400 text-[11px]">{selectedTrail.generated_artifacts?.length || 0} Files</div>
                  </div>
                </div>
              </div>

              {/* Event Trace Ledger */}
              {selectedTrail.events && selectedTrail.events.length > 0 && (
                <div className="p-6 rounded-3xl glass-panel space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-emerald-400" />
                    Chronological Execution Trace ({selectedTrail.events.length})
                  </h4>
                  <div className="space-y-2 font-mono text-xs">
                    {selectedTrail.events.map((e, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-2xl bg-obsidian-950/80 border border-white/5 flex items-center justify-between"
                      >
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-emerald-400" />
                          <span className="font-bold text-slate-200">{e.event_type}</span>
                          <span className="text-slate-500 text-[11px]">({e.source_service})</span>
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {e.duration_ms ? `${e.duration_ms.toFixed(1)}ms` : "Logged"}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-16 rounded-3xl glass-panel text-center text-slate-500">
              Select an audit trail on the left to inspect immutable provenance details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
