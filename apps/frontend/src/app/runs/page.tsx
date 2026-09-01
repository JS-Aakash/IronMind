"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { TaskResponse } from "@/lib/types";
import { StatusBadge } from "@/components/layout/StatusBadge";
import {
  Bot,
  Clock,
  ChevronRight,
  FileCode,
  CheckCircle,
  RefreshCw,
  Cpu,
  Layers,
  Wrench,
  ShieldCheck,
  FileText,
  AlertCircle,
  Terminal,
} from "lucide-react";

export default function AgentRunsPage() {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [selectedTask, setSelectedTask] = useState<TaskResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const data = await api.getTasks();
      setTasks(data);
      if (data.length > 0 && !selectedTask) {
        setSelectedTask(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-3xl glass-panel relative overflow-hidden">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Bot className="w-6 h-6 text-indigo-400" />
            <span>Agent Execution & State Machine Runs</span>
          </h2>
          <p className="text-xs md:text-sm text-slate-400">
            Chronological audit trace of autonomous lifecycles (PLAN → EXECUTE → OBSERVE → VERIFY → COMPLETE).
          </p>
        </div>
        <button
          onClick={fetchTasks}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.09] text-slate-200 text-xs font-semibold transition border border-white/10"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
          <span>Refresh Runs</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Recorded Runs List (5 Cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-400 px-1">
            <span>EXECUTED RUNS ({tasks.length})</span>
          </div>

          {tasks.length === 0 ? (
            <div className="p-12 text-center rounded-3xl glass-panel space-y-3">
              <Bot className="w-8 h-8 text-slate-600 mx-auto" />
              <div className="text-sm font-semibold text-slate-300">No agent runs recorded yet</div>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Execute a task in the Workbench to see live execution state machines here.
              </p>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[680px] overflow-y-auto pr-1">
              {tasks.map((t) => {
                const isSelected = selectedTask?.task_id === t.task_id;
                return (
                  <button
                    key={t.task_id}
                    type="button"
                    onClick={() => setSelectedTask(t)}
                    className={`w-full text-left p-4 rounded-2xl border transition space-y-2 cursor-pointer ${
                      isSelected
                        ? "bg-indigo-500/10 border-indigo-500/40 shadow-lg shadow-indigo-500/15"
                        : "glass-panel-interactive border-white/5"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="font-bold text-indigo-400">{t.task_id}</span>
                      <StatusBadge status={t.status} />
                    </div>

                    <p className="text-xs text-slate-200 line-clamp-2 leading-relaxed">
                      {t.goal}
                    </p>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-white/5">
                      <span className="capitalize">{t.task_type?.replace(/_/g, " ")}</span>
                      <span className="font-mono text-[10px]">
                        {t.plan?.length || 0} Steps
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Detailed Execution Trace (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          {selectedTask ? (
            <div className="space-y-5">
              {/* Task Header Card */}
              <div className="p-6 rounded-3xl glass-panel space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-indigo-400 font-bold">
                    {selectedTask.task_id}
                  </span>
                  <StatusBadge status={selectedTask.status} />
                </div>
                <h3 className="text-base font-bold text-white">{selectedTask.goal}</h3>
                <div className="flex flex-wrap gap-4 text-xs text-slate-400 pt-2 border-t border-white/5">
                  <div>
                    <span className="text-slate-500">Type: </span>
                    <span className="text-slate-200 font-mono">{selectedTask.task_type}</span>
                  </div>
                  {selectedTask.created_at && (
                    <div>
                      <span className="text-slate-500">Created: </span>
                      <span className="text-slate-200 font-mono">
                        {new Date(selectedTask.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Execution Steps Breakdown */}
              <div className="p-6 rounded-3xl glass-panel space-y-4">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  Planned Plan Steps ({selectedTask.plan?.length || 0})
                </h4>

                <div className="space-y-3">
                  {selectedTask.plan?.map((step, idx) => (
                    <div
                      key={step.step_id || idx}
                      className="p-4 rounded-2xl bg-obsidian-950/80 border border-white/5 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-300 flex items-center justify-center text-[10px] font-bold font-mono">
                            {idx + 1}
                          </span>
                          <span className="text-xs font-bold text-slate-100">{step.title}</span>
                        </div>
                        <StatusBadge status={step.status} />
                      </div>

                      <p className="text-xs text-slate-400 pl-7">{step.description}</p>

                      <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pl-7 pt-1">
                        <span>Model: <span className="text-indigo-400">{step.assigned_model}</span></span>
                        <span>Tool: <span className="text-cyan-400">{step.tool_name || "Direct Reasoning"}</span></span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Verified Observations */}
              {selectedTask.observations && selectedTask.observations.length > 0 && (
                <div className="p-6 rounded-3xl glass-panel space-y-3">
                  <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    Synthesized Step Observations ({selectedTask.observations.length})
                  </h4>
                  <div className="space-y-2">
                    {selectedTask.observations.map((obs, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-2xl bg-obsidian-950/80 border border-emerald-500/20 text-xs text-slate-200 font-mono leading-relaxed"
                      >
                        {typeof obs === "object" ? JSON.stringify(obs, null, 2) : String(obs)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-16 rounded-3xl glass-panel text-center text-slate-500">
              Select an agent execution run from the left list to inspect details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
