"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { SystemHealth } from "@/lib/types";
import { Cpu, RefreshCw, Layers } from "lucide-react";

export const Header = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      // Backend maybe offline
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-white/5 bg-obsidian-950/70 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center space-x-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          <Layers className="w-4 h-4 text-indigo-400" />
          <span>Intelligent Agent Orchestration</span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {health ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>System Operational</span>
            </div>
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 font-mono">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span>Local Open-Weight LLMs</span>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
            <span>Connecting...</span>
          </div>
        )}

        <button
          onClick={fetchHealth}
          className="p-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 hover:text-white border border-white/5 transition"
          title="Refresh System Status"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
        </button>
      </div>
    </header>
  );
};
