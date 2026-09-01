"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { ModelInfo } from "@/lib/types";
import { StatusBadge } from "@/components/layout/StatusBadge";
import {
  Boxes,
  Cpu,
  CheckCircle2,
  Zap,
  RefreshCw,
  Terminal,
  Play,
  Activity,
  Layers,
  Sparkles,
} from "lucide-react";

export default function ModelsPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [testPrompt, setTestPrompt] = useState("Explain centrifugal pump cavitation and NPSH limits");
  const [testResult, setTestResult] = useState<any | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  const fetchModels = async () => {
    try {
      setLoading(true);
      const data = await api.getModels();
      setModels(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleTestInference = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testPrompt.trim()) return;
    try {
      setIsTesting(true);
      setTestResult(null);
      const res = await api.testModel(testPrompt);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ error: err?.message || "Inference failed" });
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-3xl glass-panel relative overflow-hidden">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Boxes className="w-6 h-6 text-indigo-400" />
            <span>Model Gateway & Foundation Rosters</span>
          </h2>
          <p className="text-xs md:text-sm text-slate-400">
            Local open-weight foundation models allocated for vision, coding, planning, and synthesis.
          </p>
        </div>
        <button
          onClick={fetchModels}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.09] text-slate-200 text-xs font-semibold transition border border-white/10"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
          <span>Refresh Status</span>
        </button>
      </div>

      {/* Model Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {models.map((model) => (
          <div
            key={model.id}
            className="glass-panel-interactive p-6 rounded-3xl space-y-4 flex flex-col justify-between"
          >
            <div className="space-y-3">
              {/* Header Row */}
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2.5">
                    <span className="text-base font-bold text-white font-sans">{model.name}</span>
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/25 uppercase">
                      {model.role}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400">
                    Provider: <span className="text-slate-200 font-medium">{model.provider}</span>
                  </div>
                </div>

                <StatusBadge status={model.status || "LOADED"} />
              </div>

              {/* Capabilities List */}
              <div className="space-y-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Model Capabilities
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {model.capabilities.map((cap) => (
                    <span
                      key={cap}
                      className="text-[11px] px-2.5 py-1 rounded-xl bg-obsidian-950/80 text-slate-300 border border-white/5 font-mono"
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Hardware & Status Footer */}
            <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs font-mono text-slate-400">
              <div className="flex items-center gap-3 text-[11px]">
                <span>VRAM: {model.vram_usage_mb || "Dynamic"} MB</span>
                <span>Context: {model.context_length || "32k"} tokens</span>
              </div>
              <div className="text-[11px] text-emerald-400 font-medium">Ready</div>
            </div>
          </div>
        ))}
      </div>

      {/* Model Diagnostic In-Memory Test Console */}
      <div className="p-6 rounded-3xl glass-panel space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Terminal className="w-4 h-4 text-indigo-400" />
            Live Model Inference Playground
          </h4>
          <span className="text-[10px] font-mono text-indigo-400">Direct Gateway Route</span>
        </div>

        <form onSubmit={handleTestInference} className="space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={testPrompt}
              onChange={(e) => setTestPrompt(e.target.value)}
              placeholder="Input test query to probe local model latency..."
              className="flex-1 px-4 py-2.5 rounded-xl bg-obsidian-950/80 border border-white/10 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono shadow-inner"
            />
            <button
              type="submit"
              disabled={isTesting || !testPrompt.trim()}
              className="shimmer-button px-5 py-2.5 rounded-xl text-white font-semibold text-xs transition disabled:opacity-50 flex items-center gap-2 cursor-pointer shadow-lg shadow-indigo-500/25"
            >
              {isTesting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              <span>Test Prompt</span>
            </button>
          </div>
        </form>

        {testResult && (
          <div className="p-4 rounded-2xl bg-obsidian-950/80 border border-white/5 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 border-b border-white/5 pb-2">
              <span>Model: <span className="text-indigo-400 font-bold">{testResult.model || "qwen3:8b"}</span></span>
              <span>Latency: <span className="text-emerald-400">{testResult.latency_ms ? `${testResult.latency_ms.toFixed(1)}ms` : "Live"}</span></span>
              <span>Tokens: {testResult.total_tokens || testResult.completion_tokens || 0}</span>
            </div>
            <pre className="font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed max-h-56 overflow-y-auto">
              {testResult.text || JSON.stringify(testResult, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
