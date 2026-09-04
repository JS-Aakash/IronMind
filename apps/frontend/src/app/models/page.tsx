"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api-client";
import { LocalModelStatus } from "@/lib/types";
import {
  Boxes,
  Check,
  Cpu,
  Edit3,
  HardDrive,
  Info,
  RefreshCw,
  Server,
  Settings2,
  ShieldCheck,
  X,
  Zap,
} from "lucide-react";

export default function ModelsPage() {
  const [modelsStatus, setModelsStatus] = useState<LocalModelStatus[]>([]);
  const [installedModels, setInstalledModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingModelId, setLoadingModelId] = useState<string | null>(null);
  const loadingModelIdRef = useRef<string | null>(null);

  // Edit / Change model modal state
  const [selectedRoleForEdit, setSelectedRoleForEdit] = useState<LocalModelStatus | null>(null);
  const [customModelTag, setCustomModelTag] = useState("");
  const [customDisplayName, setCustomDisplayName] = useState("");
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [configureMessage, setConfigureMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Initial fetch
  const fetchStatus = async (isManual = false) => {
    try {
      if (isManual) setLoading(true);
      const [statusData, installedData] = await Promise.all([
        api.getModelsStatus().catch(() => []),
        api.getInstalledModels().catch(() => ({ models: [] })),
      ]);

      if (statusData && statusData.length > 0) {
        // If an operation is currently loading, preserve its local optimistic loading state
        const activeLoadingId = loadingModelIdRef.current;
        if (activeLoadingId) {
          setModelsStatus((prev) =>
            statusData.map((fresh) => {
              if (fresh.id === activeLoadingId) {
                const prevMatch = prev.find((p) => p.id === activeLoadingId);
                return prevMatch || fresh;
              }
              return fresh;
            })
          );
        } else {
          setModelsStatus(statusData);
        }
      }

      if (installedData?.models) {
        setInstalledModels(installedData.models);
      }
    } catch (e) {
      console.error("Failed to load models status:", e);
    } finally {
      if (isManual) setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus(true);

    // Live background polling every 4 seconds
    const interval = setInterval(() => {
      fetchStatus(false);
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  // Handle Load / Unload toggle
  const handleToggleModelLoad = async (modelId: string, currentlyWarm: boolean) => {
    try {
      setLoadingModelId(modelId);
      loadingModelIdRef.current = modelId;

      // Optimistic update
      setModelsStatus((prev) =>
        prev.map((m) => {
          if (m.id === modelId) {
            return {
              ...m,
              status: currentlyWarm ? "UNLOADED" : "LOADING",
              is_warm: !currentlyWarm,
            };
          }
          // If warming a specialist model, the other GPU model is released
          if (!currentlyWarm && modelId !== "qwen3:0.6b" && m.id !== "qwen3:0.6b") {
            return {
              ...m,
              status: "UNLOADED",
              is_warm: false,
              vram_usage_mb: 0,
            };
          }
          return m;
        })
      );

      if (currentlyWarm) {
        await api.unloadModel(modelId);
      } else {
        await api.loadModel(modelId);
      }

      const fresh = await api.getModelsStatus();
      setModelsStatus(fresh);
    } catch (err: any) {
      console.error(`Error toggling model ${modelId}:`, err);
      try {
        const fresh = await api.getModelsStatus();
        setModelsStatus(fresh);
      } catch {}
    } finally {
      setLoadingModelId(null);
      loadingModelIdRef.current = null;
    }
  };

  // Open modal to configure / change model
  const handleOpenEditModal = (model: LocalModelStatus) => {
    setSelectedRoleForEdit(model);
    setCustomModelTag(model.id);
    setCustomDisplayName(model.display_name.split(" - ")[0] || model.id);
    setConfigureMessage(null);
  };

  // Submit model change
  const handleSaveModelConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRoleForEdit || !customModelTag.trim()) return;

    try {
      setIsConfiguring(true);
      setConfigureMessage(null);

      const res = await api.configureModelRole({
        role: selectedRoleForEdit.role,
        model_tag: customModelTag.trim(),
        display_name: customDisplayName.trim() || undefined,
      });

      setConfigureMessage({
        type: "success",
        text: `Role '${selectedRoleForEdit.role.toUpperCase()}' successfully updated to '${customModelTag.trim()}'.`,
      });

      if (res.models) {
        setModelsStatus(res.models);
      } else {
        await fetchStatus(false);
      }

      setTimeout(() => {
        setSelectedRoleForEdit(null);
        setConfigureMessage(null);
      }, 1200);
    } catch (err: any) {
      console.error("Failed to reassign model role:", err);
      setConfigureMessage({
        type: "error",
        text: err?.message || "Failed to update model assignment. Verify Ollama tag.",
      });
    } finally {
      setIsConfiguring(false);
    }
  };

  // Summary calculations
  const warmCount = modelsStatus.filter((m) => m.is_warm || m.status === "LOADED • WARM").length;
  const totalAllocatedMemory = modelsStatus.reduce((acc, m) => {
    const isWarm = m.is_warm || m.status === "LOADED • WARM";
    return isWarm ? acc + (m.vram_usage_mb || 0) : acc;
  }, 0);

  // Fallback items if backend initial call is in progress
  const displayList: LocalModelStatus[] =
    modelsStatus.length > 0
      ? modelsStatus
      : [
          {
            id: "qwen3:0.6b",
            name: "qwen3:0.6b",
            display_name: "qwen3:0.6b - Router",
            description: "Ultra-lightweight 0.6B local model dedicated to low-latency capability routing and request triage.",
            role: "routing",
            status: "UNLOADED",
            is_warm: false,
            vram_usage_mb: 450,
          },
          {
            id: "qwen3:8b",
            name: "qwen3:8b",
            display_name: "qwen3:8b - Reasoning",
            description: "Primary local reasoning and orchestration model for multi-step agent planning.",
            role: "reasoning",
            status: "UNLOADED",
            is_warm: false,
            vram_usage_mb: 5000,
          },
          {
            id: "qwen2.5-coder:7b",
            name: "qwen2.5-coder:7b",
            display_name: "qwen2.5-coder:7b - Coding",
            description: "Specialized programming and script verification model for isolated sandbox execution.",
            role: "coding",
            status: "UNLOADED",
            is_warm: false,
            vram_usage_mb: 4500,
          },
          {
            id: "qwen2.5vl:7b",
            name: "qwen2.5vl:7b",
            display_name: "qwen2.5vl:7b - Vision",
            description: "On-premise multimodal vision model for inspecting P&ID drawings, charts, and scanned inspection logs.",
            role: "vision",
            status: "UNLOADED",
            is_warm: false,
            vram_usage_mb: 5500,
          },
        ];

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      {/* Header Banner */}
      <div className="p-6 md:p-8 rounded-3xl glass-panel relative overflow-hidden border border-iron-border/80 shadow-2xl">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-iron-accentPrimary/15 border border-iron-accentPrimary/30 text-iron-accentPrimary shadow-inner">
                <Boxes className="w-6 h-6" />
              </div>
              <h2 className="text-2xl md:text-3xl font-bold text-iron-textPrimary tracking-tight">
                Model Gateway & Sovereign Rosters
              </h2>
            </div>
            <p className="text-xs md:text-sm text-iron-textSecondary leading-relaxed">
              Preload, warm, and reassign local open-weight models across dedicated industrial roles.
              Changes configured here apply seamlessly across the entire IronMind execution engine and Workbench.
            </p>
          </div>

          {/* Quick Stats & Refresh */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="px-4 py-2.5 rounded-2xl bg-iron-panelSecondary/70 border border-iron-border flex items-center gap-2.5 text-xs font-mono">
              <ShieldCheck className="w-4 h-4 text-iron-success" />
              <span className="text-iron-textSecondary">Sovereignty:</span>
              <span className="text-iron-textPrimary font-bold">100% Air-Gapped</span>
            </div>

            <div className="px-4 py-2.5 rounded-2xl bg-iron-panelSecondary/70 border border-iron-border flex items-center gap-2.5 text-xs font-mono">
              <Cpu className="w-4 h-4 text-iron-accentPrimary" />
              <span className="text-iron-textSecondary">Warm in Memory:</span>
              <span className={`font-bold ${warmCount > 0 ? "text-iron-success" : "text-iron-textSecondary"}`}>
                {warmCount} / 4
              </span>
            </div>

            <button
              onClick={() => fetchStatus(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-iron-panelSecondary/80 hover:bg-iron-border/60 text-iron-textPrimary text-xs font-semibold transition border border-iron-border cursor-pointer shadow-sm active:scale-95"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-iron-accentPrimary" : ""}`} />
              <span>Refresh Status</span>
            </button>
          </div>
        </div>

        {/* Subtle decorative glow */}
        <div className="absolute -right-20 -bottom-20 w-80 h-80 bg-iron-accentPrimary/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* Role Assignment Notice */}
      <div className="flex items-start gap-3 p-4 rounded-2xl bg-iron-panelSecondary/40 border border-iron-border/60 text-xs text-iron-textSecondary">
        <Info className="w-4 h-4 text-iron-accentPrimary shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-iron-textPrimary">Dynamic Role Reassignment:</span> Use the{" "}
          <strong className="text-iron-textPrimary font-semibold">Change Model</strong> action on any card below to swap the underlying local model (e.g. swap <code className="px-1.5 py-0.5 rounded bg-iron-midnight font-mono text-[11px] text-iron-accentPrimary">qwen3:8b</code> for <code className="px-1.5 py-0.5 rounded bg-iron-midnight font-mono text-[11px] text-iron-accentPrimary">qwen3:14b</code> or any downloaded Ollama tag). The newly assigned model will be immediately used by the AI Router and Workbench.
        </div>
      </div>

      {/* Model Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {displayList.map((model) => {
          const isWarm = model.is_warm || model.status === "LOADED • WARM";
          const isLoading = loadingModelId === model.id;

          const roleBadgeColor =
            model.role === "routing"
              ? "bg-sky-500/15 text-sky-400 border-sky-500/30"
              : model.role === "reasoning"
              ? "bg-purple-500/15 text-purple-400 border-purple-500/30"
              : model.role === "coding"
              ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
              : "bg-amber-500/15 text-amber-400 border-amber-500/30";

          return (
            <div
              key={model.id}
              className={`p-6 rounded-3xl border transition-all flex flex-col justify-between space-y-5 shadow-lg ${
                isWarm
                  ? "bg-iron-panelSecondary/90 border-iron-success/50 ring-1 ring-iron-success/20 shadow-iron-success/5"
                  : "bg-iron-panel/90 border-iron-border/90 hover:border-iron-border"
              }`}
            >
              {/* Card Header */}
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <span className={`text-[11px] font-mono font-bold px-2.5 py-1 rounded-xl border uppercase tracking-wider ${roleBadgeColor}`}>
                        {model.role.toUpperCase()} ROLE
                      </span>
                      <span className="text-xs font-mono text-iron-textSecondary">
                        Ollama • Localhost
                      </span>
                    </div>

                    <h3 className="text-lg font-bold text-iron-textPrimary flex items-center gap-2 pt-1">
                      <span className="font-mono text-iron-accentPrimary">{model.id}</span>
                    </h3>
                  </div>

                  {/* Status Badge */}
                  <div>
                    {isLoading ? (
                      <span className="px-3 py-1 rounded-xl bg-iron-warning/15 border border-iron-warning/40 text-iron-warning text-xs font-mono font-bold flex items-center gap-1.5 animate-pulse">
                        <RefreshCw className="w-3 h-3 animate-spin" />
                        <span>LOADING</span>
                      </span>
                    ) : isWarm ? (
                      <span className="px-3 py-1 rounded-xl bg-iron-success/15 border border-iron-success/40 text-iron-success text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm">
                        <span className="w-2 h-2 rounded-full bg-iron-success animate-pulse" />
                        <span>LOADED • WARM</span>
                      </span>
                    ) : (
                      <span className="px-3 py-1 rounded-xl bg-iron-panelSecondary border border-iron-border text-iron-textSecondary text-xs font-mono font-semibold">
                        UNLOADED
                      </span>
                    )}
                  </div>
                </div>

                {/* Description */}
                <p className="text-xs text-iron-textSecondary leading-relaxed">
                  {model.description}
                </p>

                {/* Specifications Grid (Replacing unwanted capability labels) */}
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-iron-border/60">
                  <div className="p-3 rounded-2xl bg-iron-midnight/60 border border-iron-border/40 space-y-1">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-iron-textSecondary flex items-center gap-1.5">
                      <HardDrive className="w-3 h-3 text-iron-accentPrimary" />
                      <span>Memory Allocation</span>
                    </div>
                    <div className="text-xs font-mono font-bold text-iron-textPrimary">
                      {isWarm
                        ? model.id === "qwen3:0.6b"
                          ? "450 MB RAM (CPU)"
                          : `${model.vram_usage_mb || "4,500"} MB VRAM (GPU)`
                        : "Inactive (0 MB)"}
                    </div>
                  </div>

                  <div className="p-3 rounded-2xl bg-iron-midnight/60 border border-iron-border/40 space-y-1">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-iron-textSecondary flex items-center gap-1.5">
                      <Server className="w-3 h-3 text-iron-accentSecondary" />
                      <span>Context Window</span>
                    </div>
                    <div className="text-xs font-mono font-bold text-iron-textPrimary">
                      {model.role === "routing" ? "8,192 tokens" : "32,768 tokens"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-iron-border/60 flex items-center gap-3">
                {/* Load / Unload Toggle */}
                {isWarm ? (
                  <button
                    type="button"
                    disabled={isLoading}
                    onClick={() => handleToggleModelLoad(model.id, true)}
                    className="flex-1 py-2.5 px-4 rounded-xl bg-iron-error/15 hover:bg-iron-error/25 text-iron-error border border-iron-error/30 text-xs font-mono font-semibold transition cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {isLoading ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <X className="w-3.5 h-3.5" />
                    )}
                    <span>Unload Model</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled={isLoading}
                    onClick={() => handleToggleModelLoad(model.id, false)}
                    className="flex-1 py-2.5 px-4 rounded-xl bg-iron-accentPrimary/15 hover:bg-iron-accentPrimary/25 text-iron-accentPrimary border border-iron-accentPrimary/30 text-xs font-mono font-semibold transition cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {isLoading ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Zap className="w-3.5 h-3.5" />
                    )}
                    <span>Load Warm in Memory</span>
                  </button>
                )}

                {/* Change Model Button */}
                <button
                  type="button"
                  onClick={() => handleOpenEditModal(model)}
                  className="py-2.5 px-4 rounded-xl bg-iron-panelSecondary hover:bg-iron-border text-iron-textPrimary border border-iron-border text-xs font-mono font-semibold transition cursor-pointer flex items-center justify-center gap-2 active:scale-95"
                  title="Change model tag assigned to this role"
                >
                  <Settings2 className="w-3.5 h-3.5 text-iron-accentSecondary" />
                  <span>Change Model</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Change Model Modal / Drawer */}
      {selectedRoleForEdit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg p-6 rounded-3xl bg-iron-panel border border-iron-border shadow-2xl space-y-6 relative">
            {/* Modal Header */}
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Settings2 className="w-5 h-5 text-iron-accentPrimary" />
                  <h3 className="text-lg font-bold text-iron-textPrimary">
                    Reassign {selectedRoleForEdit.role.toUpperCase()} Model
                  </h3>
                </div>
                <p className="text-xs text-iron-textSecondary">
                  Select an installed Ollama model or specify any custom tag. This model will take over the{" "}
                  <span className="font-semibold text-iron-accentPrimary font-mono">{selectedRoleForEdit.role}</span> role across the entire system.
                </p>
              </div>

              <button
                onClick={() => setSelectedRoleForEdit(null)}
                className="p-1.5 rounded-lg hover:bg-iron-panelSecondary text-iron-textSecondary hover:text-white transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Notification / Feedback Banner */}
            {configureMessage && (
              <div
                className={`p-3.5 rounded-xl text-xs font-mono flex items-center gap-2 ${
                  configureMessage.type === "success"
                    ? "bg-iron-success/15 border border-iron-success/40 text-iron-success"
                    : "bg-iron-error/15 border border-iron-error/40 text-iron-error"
                }`}
              >
                {configureMessage.type === "success" ? (
                  <Check className="w-4 h-4 shrink-0" />
                ) : (
                  <X className="w-4 h-4 shrink-0" />
                )}
                <span>{configureMessage.text}</span>
              </div>
            )}

            <form onSubmit={handleSaveModelConfig} className="space-y-4">
              {/* Quick Select from Installed Models */}
              {installedModels.length > 0 && (
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-iron-textPrimary flex items-center justify-between">
                    <span>Installed Ollama Models</span>
                    <span className="text-[10px] text-iron-textSecondary font-mono">
                      {installedModels.length} detected locally
                    </span>
                  </label>
                  <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto pr-1">
                    {installedModels.map((tag) => (
                      <button
                        key={tag}
                        type="button"
                        onClick={() => {
                          setCustomModelTag(tag);
                          setCustomDisplayName(`${tag.split(":")[0].toUpperCase()} (${tag.split(":")[1] || "Default"})`);
                        }}
                        className={`p-2.5 rounded-xl border text-left text-xs font-mono transition flex items-center justify-between cursor-pointer ${
                          customModelTag === tag
                            ? "bg-iron-accentPrimary/20 border-iron-accentPrimary text-iron-accentPrimary font-bold"
                            : "bg-iron-panelSecondary/60 border-iron-border/60 text-iron-textSecondary hover:text-iron-textPrimary hover:border-iron-border"
                        }`}
                      >
                        <span className="truncate">{tag}</span>
                        {customModelTag === tag && <Check className="w-3.5 h-3.5 shrink-0" />}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Model Tag Input */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-iron-textPrimary">
                  Model Identifier / Tag <span className="text-iron-error">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={customModelTag}
                  onChange={(e) => setCustomModelTag(e.target.value)}
                  placeholder="e.g. qwen3:14b, qwen2.5-coder:14b, llama3.3:70b"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-iron-panelSecondary border border-iron-border text-iron-textPrimary text-xs font-mono focus:outline-none focus:border-iron-accentPrimary"
                />
                <p className="text-[11px] text-iron-textSecondary">
                  Must match the exact model name/tag registered in your local Ollama instance.
                </p>
              </div>

              {/* Display Name Input */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-iron-textPrimary">
                  Display Label <span className="text-iron-textSecondary text-[11px]">(Optional)</span>
                </label>
                <input
                  type="text"
                  value={customDisplayName}
                  onChange={(e) => setCustomDisplayName(e.target.value)}
                  placeholder="e.g. Qwen 3 (14B High-Order Reasoning)"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-iron-panelSecondary border border-iron-border text-iron-textPrimary text-xs focus:outline-none focus:border-iron-accentPrimary"
                />
              </div>

              {/* Modal Footer Actions */}
              <div className="pt-4 border-t border-iron-border/60 flex items-center justify-end gap-3">
                <button
                  type="button"
                  disabled={isConfiguring}
                  onClick={() => setSelectedRoleForEdit(null)}
                  className="px-4 py-2 rounded-xl text-xs text-iron-textSecondary hover:text-white transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isConfiguring || !customModelTag.trim()}
                  className="px-5 py-2.5 rounded-xl bg-iron-accentPrimary hover:bg-iron-accentPrimary/90 text-white text-xs font-semibold font-mono transition cursor-pointer flex items-center gap-2 disabled:opacity-50 shadow-md shadow-iron-accentPrimary/20"
                >
                  {isConfiguring ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Check className="w-3.5 h-3.5" />
                  )}
                  <span>Apply & Reassign Role</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
