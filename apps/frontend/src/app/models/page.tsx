"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { ModelInfo } from "@/lib/types";
import { StatusBadge } from "@/components/layout/StatusBadge";
import {
  Boxes,
  RefreshCw,
} from "lucide-react";

export default function ModelsPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);

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

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-3xl glass-panel relative overflow-hidden">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Boxes className="w-6 h-6 text-palette-periwinkle" />
            <span>Model Gateway & Foundation Rosters</span>
          </h2>
          <p className="text-xs md:text-sm text-palette-ice/80">
            Local open-weight foundation models allocated for vision, coding, planning, and synthesis.
          </p>
        </div>
        <button
          onClick={fetchModels}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-palette-violet/30 hover:bg-palette-violet/60 text-palette-ice text-xs font-semibold transition border border-palette-periwinkle/20 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-palette-periwinkle" : ""}`} />
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
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-palette-royal/25 text-palette-periwinkle border border-palette-periwinkle/30 uppercase">
                      {model.role}
                    </span>
                  </div>
                  <div className="text-xs text-palette-ice/70">
                    Provider: <span className="text-slate-200 font-medium">{model.provider}</span>
                  </div>
                </div>

                <StatusBadge status={model.status || "LOADED"} />
              </div>

              {/* Capabilities List */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {model.capabilities.map((cap) => (
                  <span
                    key={cap}
                    className="text-[11px] px-2.5 py-1 rounded-xl bg-palette-midnight/80 text-palette-ice border border-palette-periwinkle/15 font-mono"
                  >
                    {cap}
                  </span>
                ))}
              </div>
            </div>

            {/* Hardware & Status Footer */}
            <div className="pt-3 border-t border-palette-periwinkle/15 flex items-center justify-between text-xs font-mono text-palette-ice/60">
              <div className="flex items-center gap-3 text-[11px]">
                <span>VRAM: {model.vram_usage_mb || "Dynamic"} MB</span>
                <span>Context: {model.context_length || "32k"} tokens</span>
              </div>
              <div className="text-[11px] text-emerald-400 font-medium">Ready</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
