"use client";

import Link from "next/link";
import { ShieldCheck, Lock, Activity, WifiOff, Cpu } from "lucide-react";

export const Header = () => {
  return (
    <header className="h-16 border-b border-slate-800/80 bg-[#080D1A]/95 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20 shadow-[0_4px_20px_rgba(0,0,0,0.4)]">
      {/* Brand & High-Tech Sovereign Title Bar */}
      <div className="flex items-center space-x-3.5">
        <div className="relative flex items-center justify-center">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500/20 via-indigo-600/15 to-cyan-500/20 border border-sky-500/40 flex items-center justify-center shadow-[0_0_15px_rgba(14,165,233,0.25)]">
            <ShieldCheck className="w-5 h-5 text-sky-400" />
          </div>
          <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </div>

        <div>
          <div className="flex items-center gap-2.5">
            <span className="font-extrabold text-base tracking-wider bg-gradient-to-r from-white via-slate-100 to-sky-300 bg-clip-text text-transparent font-sans">
              IRONMIND
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-950/80 text-sky-300 border border-sky-500/40 font-bold tracking-wider shadow-[0_0_10px_rgba(14,165,233,0.2)] flex items-center gap-1">
              <Lock className="w-2.5 h-2.5 text-sky-400" />
              AIR-GAP ENFORCED
            </span>
            <span className="hidden lg:inline-flex text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-850 text-slate-300 border border-slate-700 font-semibold">
              LOCAL HARDWARE CLUSTER
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono tracking-tight">
            Sovereign Industrial AI Workbench • 100% Confidential On-Premise Execution
          </p>
        </div>
      </div>

      {/* Live Air-Gap Security Telemetry Strip */}
      <div className="flex items-center space-x-3">
        {/* Zero Egress Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/90 border border-slate-700/80 text-slate-300 text-xs font-mono font-medium shadow-sm">
          <WifiOff className="w-3.5 h-3.5 text-sky-400" />
          <span>0 CLOUD EGRESS</span>
        </div>

        {/* Local Inference Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-sky-950/40 border border-sky-500/30 text-sky-300 text-xs font-mono font-semibold">
          <Cpu className="w-3.5 h-3.5 text-sky-400" />
          <span>LOCAL SILICON</span>
        </div>

        {/* Quick Link to Sovereignty Page */}
        <Link
          href="/sovereignty"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0F172A] hover:bg-sky-950/30 text-slate-300 hover:text-sky-300 border border-slate-700/60 hover:border-sky-500/40 text-xs font-mono transition shadow-sm"
          title="Inspect Zero-Egress Network Cryptography"
        >
          <Activity className="w-3.5 h-3.5 text-sky-400" />
          <span className="font-semibold">Security Matrix</span>
        </Link>
      </div>
    </header>
  );
};
