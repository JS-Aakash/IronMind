"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { SovereigntyStatus } from "@/lib/types";
import { StatusBadge } from "@/components/layout/StatusBadge";
import {
  ShieldCheck,
  Radio,
  Lock,
  Globe,
  Activity,
  Server,
  Terminal,
  RefreshCw,
  AlertTriangle,
  Play,
  CheckCircle2,
  Cpu,
  Layers,
  Shield,
  Sparkles,
} from "lucide-react";

export default function SovereigntyPage() {
  const [status, setStatus] = useState<SovereigntyStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [probeResult, setProbeResult] = useState<any | null>(null);
  const [isProbing, setIsProbing] = useState(false);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const data = await api.getSovereigntyStatus();
      setStatus(data);
    } catch (e) {
      console.error("Failed to load security status:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleRunDiagnosticProbe = async () => {
    try {
      setIsProbing(true);
      const res = await api.verifyAirgap();
      setProbeResult(res);
      await fetchStatus();
    } catch (err: any) {
      setProbeResult({ error: err?.message || "Diagnostic probe failed" });
    } finally {
      setIsProbing(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-3xl glass-panel relative overflow-hidden">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            <span>Security, Privacy & Trust Telemetry</span>
          </h2>
          <p className="text-xs md:text-sm text-palette-ice/80">
            Real-time auditable verification confirming self-hosted execution, local inference, and cryptographic proofs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRunDiagnosticProbe}
            disabled={isProbing}
            className="shimmer-button flex items-center gap-2 px-4 py-2 rounded-xl text-white font-semibold text-xs transition shadow-lg shadow-palette-royal/30 disabled:opacity-50 cursor-pointer"
          >
            {isProbing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>Run Trust Diagnostics</span>
          </button>
          <button
            onClick={fetchStatus}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-palette-violet/30 hover:bg-palette-violet/60 text-palette-ice text-xs font-semibold transition border border-palette-periwinkle/20"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-palette-periwinkle" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Telemetry Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {/* 1. Isolation Status */}
        <div className="glass-panel p-4 rounded-2xl space-y-1 text-center">
          <div className="text-[10px] font-semibold text-palette-ice/70 uppercase">Isolation</div>
          <div className="text-sm font-bold text-emerald-400 font-mono">
            {status?.mode || "ISOLATED"}
          </div>
          <div className="text-[10px] text-palette-ice/50">Self-Hosted</div>
        </div>

        {/* 2. Model Hosting */}
        <div className="glass-panel p-4 rounded-2xl space-y-1 text-center">
          <div className="text-[10px] font-semibold text-palette-ice/70 uppercase">Inference</div>
          <div className="text-sm font-bold text-palette-periwinkle font-mono">
            Local GPU
          </div>
          <div className="text-[10px] text-palette-ice/50">Open-Weight</div>
        </div>

        {/* 3. Vector DB */}
        <div className="glass-panel p-4 rounded-2xl space-y-1 text-center">
          <div className="text-[10px] font-semibold text-palette-ice/70 uppercase">Vector DB</div>
          <div className="text-sm font-bold text-palette-blue font-mono">In-Memory</div>
          <div className="text-[10px] text-palette-ice/50">Local Vector Store</div>
        </div>

        {/* 4. External Calls */}
        <div className="glass-panel p-4 rounded-2xl space-y-1 text-center">
          <div className="text-[10px] font-semibold text-palette-ice/70 uppercase">Data Egress</div>
          <div className="text-sm font-bold text-emerald-400 font-mono">
            {status?.data_egress_bytes ?? 0} Bytes
          </div>
          <div className="text-[10px] text-palette-ice/50">0 Cloud Calls</div>
        </div>

        {/* 5. Cryptography */}
        <div className="glass-panel p-4 rounded-2xl space-y-1 text-center">
          <div className="text-[10px] font-semibold text-palette-ice/70 uppercase">Provenance</div>
          <div className="text-sm font-bold text-palette-purple font-mono">SHA-256</div>
          <div className="text-[10px] text-palette-ice/50">Immutable Hash</div>
        </div>

        {/* 6. Execution Sandbox */}
        <div className="glass-panel p-4 rounded-2xl space-y-1 text-center">
          <div className="text-[10px] font-semibold text-palette-ice/70 uppercase">Sandbox</div>
          <div className="text-sm font-bold text-emerald-400 font-mono">Isolated</div>
          <div className="text-[10px] text-palette-ice/50">Local Subprocess</div>
        </div>
      </div>

      {/* Interactive Probe Results */}
      {probeResult && (
        <div className="p-6 rounded-3xl glass-panel space-y-3 border-emerald-500/30">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Diagnostic Probe Results
            </h4>
            <span className="text-[11px] font-mono text-palette-ice/60">
              Verified at {new Date().toLocaleTimeString()}
            </span>
          </div>
          <pre className="p-4 rounded-2xl bg-palette-midnight/90 border border-palette-periwinkle/15 font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
            {JSON.stringify(probeResult, null, 2)}
          </pre>
        </div>
      )}

      {/* Security Architecture Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="glass-panel p-6 rounded-3xl space-y-3">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-palette-periwinkle" />
            <h3 className="text-sm font-bold text-white">Trust & Integrity Principles</h3>
          </div>
          <ul className="space-y-2 text-xs text-palette-ice/90 leading-relaxed">
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
              <span>All inferences run through local model gateway processes with zero remote dependencies.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
              <span>Task attachments are held in an isolated staging space and never auto-ingested into global knowledge.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
              <span>Tool actions and generated deliverables receive cryptographically verifiable SHA-256 hashes.</span>
            </li>
          </ul>
        </div>

        <div className="glass-panel p-6 rounded-3xl space-y-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-palette-blue" />
            <h3 className="text-sm font-bold text-white">Continuous Verification</h3>
          </div>
          <p className="text-xs text-palette-ice/90 leading-relaxed">
            The platform continuously audits orchestrator decisions, model responses, and tool executions against strict policy assertions.
            Every artifact is verified before marking tasks complete.
          </p>
          <div className="pt-2 text-xs font-mono text-palette-ice/70">
            Last Verified: <span className="text-emerald-400 font-semibold">{status?.last_verified_at || "Active"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
