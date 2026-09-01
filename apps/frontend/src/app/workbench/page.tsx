"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/lib/api-client";
import { RoutingDecision, TaskResponse } from "@/lib/types";
import { StatusBadge } from "@/components/layout/StatusBadge";
import {
  Send,
  Boxes,
  CheckCircle2,
  AlertCircle,
  FileCode,
  Zap,
  ArrowRight,
  Eye,
  Terminal,
  Cpu,
  Layers,
  Search,
  Download,
  Clock,
  Sparkles,
  RefreshCw,
  FileCheck,
  Paperclip,
  X,
  Image as ImageIcon,
  FileType,
  FileText,
} from "lucide-react";

interface StagedAttachment {
  filename: string;
  sizeBytes?: number;
  isUploaded?: boolean;
}

export default function WorkbenchPage() {
  const [goal, setGoal] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<StagedAttachment[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const [isRouting, setIsRouting] = useState(false);
  const [routingDecision, setRoutingDecision] = useState<RoutingDecision | null>(null);
  const [activeTask, setActiveTask] = useState<TaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const taskFileInputRef = useRef<HTMLInputElement>(null);

  const WORKFLOW_STAGES = [
    { key: "PLANNING", label: "Planning" },
    { key: "TASK_CLASSIFICATION", label: "Classification" },
    { key: "MODEL_SELECTED", label: "Model Selection" },
    { key: "DOCUMENT_PROCESSING", label: "Document/Vision" },
    { key: "KNOWLEDGE_RETRIEVAL", label: "Knowledge RAG" },
    { key: "REASONING", label: "Reasoning" },
    { key: "VERIFICATION", label: "Verification" },
    { key: "ARTIFACT_GENERATED", label: "Deliverable" },
  ];

  const samplePresets = [
    {
      id: "preset_1",
      title: "Inspection & Formal Approval Note",
      file: "MRPL_P101_Inspection_Scan.pdf",
      prompt: "Analyze scanned inspection report for Slurry Pump P-101. Cross-reference Maintenance SOP and generate formal Approval Note DOCX.",
    },
    {
      id: "preset_2",
      title: "Pump Efficiency & Sandboxed Testing",
      file: "",
      prompt: "Write a verified Python calculation module for refinery pump hydraulic efficiency with boundary assertions and verify in execution sandbox.",
    },
    {
      id: "preset_3",
      title: "P&ID Engineering Diagram Analysis",
      file: "CDU1_Plant_PID_Drawing.png",
      prompt: "Parse Crude Distillation Unit P&ID diagram to extract all pressure transmitter (PT) tags and connected relief valve dependencies.",
    },
  ];

  useEffect(() => {
    if (!goal.trim() || goal.length < 6) {
      setRoutingDecision(null);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setIsRouting(true);
        const decision = await api.selectRouter({
          goal,
          attached_files: attachedFiles.map((f) => f.filename),
        });
        setRoutingDecision(decision);
      } catch (err) {
        console.error("Routing resolution error:", err);
      } finally {
        setIsRouting(false);
      }
    }, 350);

    return () => clearTimeout(timer);
  }, [goal, attachedFiles]);

  const handleApplyPreset = (preset: (typeof samplePresets)[0]) => {
    setGoal(preset.prompt);
    if (preset.file) {
      setAttachedFiles([{ filename: preset.file, isUploaded: true }]);
    } else {
      setAttachedFiles([]);
    }
  };

  const handleTaskFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    try {
      setIsUploadingFile(true);
      setError(null);

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const res = await api.uploadTaskDocument(file);
        setAttachedFiles((prev) => [
          ...prev.filter((f) => f.filename !== res.filename),
          {
            filename: res.filename,
            sizeBytes: res.size_bytes,
            isUploaded: true,
          },
        ]);
      }
    } catch (err: any) {
      console.error("File upload failed:", err);
      setError("Failed to upload file to workspace staging area.");
    } finally {
      setIsUploadingFile(false);
      if (taskFileInputRef.current) {
        taskFileInputRef.current.value = "";
      }
    }
  };

  const handleRemoveFile = (filename: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f.filename !== filename));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;

    try {
      setIsSubmitting(true);
      setError(null);
      const files = attachedFiles.map((f) => f.filename);

      const created = await api.createTask({
        goal,
        task_type: routingDecision?.task_type || "document_analysis",
        uploaded_files: files,
      });
      setActiveTask(created);

      const executed = await api.executeTask(created.task_id, { uploaded_files: files });
      setActiveTask(executed);
    } catch (err: any) {
      setError(err?.message || "Task execution failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase();
    if (["png", "jpg", "jpeg", "bmp", "svg", "webp"].includes(ext || "")) {
      return <ImageIcon className="w-3.5 h-3.5 text-purple-400" />;
    }
    if (["pdf"].includes(ext || "")) {
      return <FileText className="w-3.5 h-3.5 text-rose-400" />;
    }
    if (["docx", "doc"].includes(ext || "")) {
      return <FileType className="w-3.5 h-3.5 text-blue-400" />;
    }
    return <FileCode className="w-3.5 h-3.5 text-cyan-400" />;
  };

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Top Banner Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-3xl glass-panel relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="space-y-1 z-10">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Cpu className="w-6 h-6 text-indigo-400" />
            <span>Interactive Agent Workbench</span>
          </h2>
          <p className="text-xs md:text-sm text-slate-400">
            Autonomous multi-stage reasoning pipeline with deterministic capability routing and verified deliverables.
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300 font-medium">
          <Zap className="w-3.5 h-3.5 text-indigo-400" />
          <span>Local Engine Standby</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Form & Routing (5 Cols) */}
        <div className="lg:col-span-5 space-y-5">
          {/* Quick Presets */}
          <div className="space-y-2.5">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Quick Task Templates
            </span>
            <div className="grid grid-cols-1 gap-2">
              {samplePresets.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleApplyPreset(p)}
                  className="text-left p-3.5 rounded-2xl glass-panel-interactive transition text-xs space-y-1 cursor-pointer group"
                >
                  <div className="font-semibold text-slate-100 group-hover:text-indigo-300 transition-colors flex items-center justify-between">
                    <span>{p.title}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
                  </div>
                  <div className="text-slate-400 text-[11px] line-clamp-1">{p.prompt}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Goal Input & File Upload Form */}
          <form onSubmit={handleSubmit} className="p-6 rounded-3xl glass-panel space-y-4">
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300">
                Task Specification / Goal
              </label>
              <textarea
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="Describe your technical objective or question (e.g. 'Analyze this photo and describe all visible features')..."
                className="w-full h-32 px-4 py-3 rounded-2xl bg-obsidian-950/80 border border-white/10 text-slate-100 placeholder-slate-500 text-xs focus:outline-none focus:border-indigo-500/60 transition resize-none leading-relaxed shadow-inner"
                required
              />
            </div>

            {/* Task-Specific File Attachments */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold text-slate-300">
                  Task Attachments
                </label>
                <span className="text-[10px] text-slate-500 font-mono">PDF, PNG, JPG, DOCX</span>
              </div>

              {/* Upload Input & Actions */}
              <div className="flex items-center gap-2">
                <input
                  ref={taskFileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.png,.jpg,.jpeg,.docx,.doc,.txt"
                  onChange={handleTaskFileUpload}
                  className="hidden"
                />
                <button
                  type="button"
                  disabled={isUploadingFile}
                  onClick={() => taskFileInputRef.current?.click()}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-obsidian-950/80 border border-dashed border-white/15 hover:border-indigo-500/50 text-slate-300 hover:text-white text-xs font-medium transition cursor-pointer"
                >
                  {isUploadingFile ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                  ) : (
                    <Paperclip className="w-3.5 h-3.5 text-indigo-400" />
                  )}
                  <span>{isUploadingFile ? "Uploading File..." : "Attach File or Image"}</span>
                </button>
              </div>

              {/* Attached Files List Chips */}
              {attachedFiles.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {attachedFiles.map((f, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-obsidian-950 border border-indigo-500/30 text-xs text-slate-200"
                    >
                      {getFileIcon(f.filename)}
                      <span className="truncate max-w-[180px] font-medium">{f.filename}</span>
                      {f.sizeBytes && (
                        <span className="text-[10px] text-slate-500 font-mono">({(f.sizeBytes / 1024).toFixed(0)}KB)</span>
                      )}
                      <button
                        type="button"
                        onClick={() => handleRemoveFile(f.filename)}
                        className="text-slate-500 hover:text-rose-400 transition"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !goal.trim()}
              className="w-full shimmer-button flex items-center justify-center gap-2 py-3.5 rounded-xl text-white font-semibold text-xs transition disabled:opacity-50 cursor-pointer shadow-lg shadow-indigo-500/25"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Orchestrating Agent Workflow...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Execute Task</span>
                </>
              )}
            </button>
          </form>

          {/* Model-Routing Explanation Panel */}
          {routingDecision && (
            <div className="p-5 rounded-3xl glass-panel space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Boxes className="w-4 h-4 text-indigo-400" />
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Model Routing Plan
                  </h4>
                </div>
                <StatusBadge status={routingDecision.task_type} />
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {routingDecision.routing_reason}
              </p>

              <div className="space-y-2 pt-2 border-t border-white/5">
                {routingDecision.stages?.map((st, i) => (
                  <div key={i} className="p-3 rounded-xl bg-obsidian-950/70 border border-white/5 text-xs space-y-1">
                    <div className="flex items-center justify-between font-mono text-[11px]">
                      <span className="text-slate-300 font-semibold">{st.stage_name}</span>
                      <span className="text-indigo-400 font-bold">{st.selected_model}</span>
                    </div>
                    <p className="text-slate-400 text-[11px] leading-relaxed">{st.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Execution State Machine Timeline & Evidence (7 Cols) */}
        <div className="lg:col-span-7 space-y-5">
          {error && (
            <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-xs text-rose-300 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-rose-200">Execution Error</h4>
                <p>{error}</p>
              </div>
            </div>
          )}

          {activeTask ? (
            <div className="space-y-5">
              {/* Task Status Banner */}
              <div className="p-6 rounded-3xl glass-panel flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-indigo-400 font-bold">{activeTask.task_id}</span>
                    <span className="text-xs text-slate-500">•</span>
                    <span className="text-xs text-slate-400 font-mono">
                      {activeTask.task_type?.toUpperCase() || "AUTONOMOUS_PIPELINE"}
                    </span>
                  </div>
                  <h3 className="font-bold text-sm text-slate-100">{activeTask.goal}</h3>
                </div>
                <StatusBadge status={activeTask.status} />
              </div>

              {/* Sequential Execution Timeline */}
              <div className="p-6 rounded-3xl glass-panel space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Execution Stage Progress
                  </h4>
                  <span className="text-xs font-mono text-slate-400">
                    Status: <span className="text-indigo-400 font-bold uppercase">{activeTask.status}</span>
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  {WORKFLOW_STAGES.map((stage, idx) => {
                    const isCompleted =
                      activeTask.status === "completed" ||
                      (activeTask.current_step_index !== undefined && activeTask.current_step_index >= idx);
                    const isFailed =
                      activeTask.status === "failed" && idx >= (activeTask.current_step_index || 0);

                    return (
                      <div
                        key={stage.key}
                        className={`p-3 rounded-2xl border transition flex flex-col justify-between space-y-1.5 ${
                          isCompleted
                            ? "bg-indigo-500/10 border-indigo-500/30 text-indigo-200"
                            : isFailed
                            ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
                            : "bg-obsidian-950/40 border-white/5 text-slate-500"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono font-bold">
                            {String(idx + 1).padStart(2, "0")}
                          </span>
                          {isCompleted ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />
                          ) : isFailed ? (
                            <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                          ) : (
                            <Clock className="w-3.5 h-3.5 text-slate-600" />
                          )}
                        </div>
                        <div className="text-xs font-semibold">{stage.label}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Sandboxed Tool Executions */}
              {activeTask.tool_calls && activeTask.tool_calls.length > 0 && (
                <div className="p-6 rounded-3xl glass-panel space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-emerald-400" />
                    Tool Invocations ({activeTask.tool_calls.length})
                  </h4>
                  <div className="space-y-2">
                    {activeTask.tool_calls.map((t, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-2xl bg-obsidian-950/80 border border-white/5 flex items-center justify-between text-xs font-mono"
                      >
                        <div className="flex items-center gap-2.5">
                          <span className="w-2 h-2 rounded-full bg-emerald-400" />
                          <span className="font-bold text-slate-200">{t.tool_name}</span>
                        </div>
                        <div className="flex items-center gap-3 text-slate-400 text-[11px]">
                          <span>{t.latency_ms?.toFixed(1)}ms</span>
                          <span className={t.success ? "text-emerald-400 font-bold" : "text-rose-400"}>
                            {t.success ? "SUCCESS" : "ERROR"}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Retrieved Grounded Evidence */}
              {activeTask.retrieved_context && activeTask.retrieved_context.length > 0 && (
                <div className="p-6 rounded-3xl glass-panel space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Search className="w-4 h-4 text-cyan-400" />
                    Retrieved Knowledge Evidence & Citations
                  </h4>
                  <div className="p-3 rounded-2xl bg-obsidian-950/80 border border-white/5 text-xs text-slate-300 space-y-2.5">
                    {activeTask.retrieved_context.map((ctx: any, i: number) => {
                      const docName =
                        typeof ctx === "object"
                          ? ctx.document_name || ctx.document || "Knowledge Reference"
                          : "Evidence Reference";
                      const pageNum =
                        typeof ctx === "object" && (ctx.page_number || ctx.page)
                          ? ` (Page ${ctx.page_number || ctx.page})`
                          : "";
                      const sectionName =
                        typeof ctx === "object" && ctx.section ? ` - ${ctx.section}` : "";
                      const textSnippet =
                        typeof ctx === "object"
                          ? ctx.text || ctx.snippet || JSON.stringify(ctx)
                          : String(ctx);
                      const scoreVal =
                        typeof ctx === "object" && (ctx.score || ctx.relevance)
                          ? ctx.score || ctx.relevance
                          : null;

                      return (
                        <div
                          key={i}
                          className="p-3.5 rounded-xl bg-obsidian-900/60 border border-cyan-500/20 space-y-1.5"
                        >
                          <div className="flex items-center justify-between text-[11px] font-mono text-cyan-400 font-bold">
                            <span>
                              {docName}
                              {pageNum}
                              {sectionName}
                            </span>
                            {scoreVal !== null && (
                              <span className="text-slate-400 font-normal">
                                Match: {typeof scoreVal === "number" ? Math.round(scoreVal * 100) : scoreVal}%
                              </span>
                            )}
                          </div>
                          <pre className="font-sans text-[12px] whitespace-pre-wrap leading-relaxed text-slate-200">
                            {textSnippet}
                          </pre>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Generated Business Deliverables */}
              {activeTask.generated_artifacts && activeTask.generated_artifacts.length > 0 && (
                <div className="p-6 rounded-3xl glass-panel space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <FileCheck className="w-4 h-4 text-emerald-400" />
                    Generated Deliverables ({activeTask.generated_artifacts.length})
                  </h4>
                  <div className="space-y-2">
                    {activeTask.generated_artifacts.map((art, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-4 rounded-2xl bg-obsidian-950/80 border border-emerald-500/25 hover:border-emerald-500/50 transition"
                      >
                        <div className="space-y-1">
                          <div className="font-semibold text-xs text-slate-100 flex items-center gap-2">
                            <FileText className="w-4 h-4 text-emerald-400" />
                            <span>{art.filename || `Deliverable_${idx + 1}`}</span>
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            SHA-256:{" "}
                            {art.sha256_hash ? `${art.sha256_hash.slice(0, 16)}...` : "VERIFIED_LOCAL"}
                          </div>
                        </div>

                        {art.download_url ? (
                          <a
                            href={`http://127.0.0.1:8000${art.download_url}`}
                            download
                            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition cursor-pointer shadow-md shadow-emerald-500/20"
                          >
                            <Download className="w-3.5 h-3.5" />
                            <span>Download</span>
                          </a>
                        ) : (
                          <span className="text-[11px] font-mono text-emerald-400">Ready in artifacts ledger</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Final Verified Executive Summary */}
              {activeTask.observations && activeTask.observations.length > 0 && (
                <div className="p-6 rounded-3xl glass-panel space-y-3 border-indigo-500/30">
                  <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                    Verified Synthesis & Findings
                  </h4>
                  <div className="p-4 rounded-2xl bg-obsidian-950/80 text-xs text-slate-200 space-y-2 leading-relaxed">
                    {activeTask.observations.map((obs: any, i: number) => (
                      <div key={i} className="text-xs whitespace-pre-wrap font-mono leading-relaxed">
                        {typeof obs === "object" ? JSON.stringify(obs, null, 2) : String(obs)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-16 rounded-3xl glass-panel text-center space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto">
                <Cpu className="w-7 h-7" />
              </div>
              <div className="space-y-1">
                <h4 className="font-bold text-base text-slate-200">Workbench Ready</h4>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Select a template on the left or enter a custom prompt with attached files to run the autonomous agent pipeline.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
