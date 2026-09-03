"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { SystemHealth } from "@/lib/types";
import { RefreshCw, ShieldCheck } from "lucide-react";

export const Header = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(false);

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
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-iron-border bg-iron-bg px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center space-x-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-base tracking-tight text-iron-textPrimary">IronMind</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-accentPrimary border border-iron-border font-medium">
              AIR-GAPPED
            </span>
          </div>
          <p className="text-[11px] text-iron-textSecondary font-normal">Sovereign AI Workbench</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-iron-panel border border-iron-border text-xs">
          <span className="w-2 h-2 rounded-full bg-iron-success animate-pulse" />
          <span className="text-iron-textPrimary font-medium text-[11px]">SYSTEM OPERATIONAL</span>
        </div>

        <button
          onClick={fetchHealth}
          className="p-2 rounded-lg bg-iron-panel hover:bg-iron-panelSecondary text-iron-textSecondary hover:text-iron-textPrimary border border-iron-border transition"
          title="Refresh System Status"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-iron-accentPrimary" : ""}`} />
        </button>
      </div>
    </header>
  );
};
