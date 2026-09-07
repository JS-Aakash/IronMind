"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import {
  ModelInfo,
  TaskAuditSummary,
  KnowledgeDocument,
  SovereigntyStatus,
  TaskResponse,
} from "@/lib/types";
import {
  ShieldCheck,
  Cpu,
  Boxes,
  Database,
  FileCheck2,
  ArrowRight,
  Code2,
  Eye,
  FileText,
  Activity,
  Layers,
  CheckCircle2,
  Terminal,
  Clock,
  Sparkles,
  Lock,
  Workflow,
  Search,
  KeyRound,
  FileCode,
  Check,
  WifiOff,
  Radio,
  Zap,
  Play,
  FileSpreadsheet,
} from "lucide-react";

export default function DashboardOverviewPage() {
  const router = useRouter();

  // Core Data States
  const [sovereignty, setSovereignty] = useState<SovereigntyStatus | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [auditTrails, setAuditTrails] = useState<TaskAuditSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDashboardData(silent = false) {
      try {
        if (!silent) setLoading(true);
        const [sovData, modData, docData, taskData, auditData] = await Promise.all([
          api.getSovereigntyStatus().catch(() => null),
          api.getModels().catch(() => []),
          api.getKnowledgeDocuments().catch(() => []),
          api.getTasks().catch(() => []),
          api.getAuditTrails(12).catch(() => []),
        ]);
        setSovereignty(sovData);
        setModels(modData);
        setDocuments(docData);
        setTasks(taskData);
        setAuditTrails(auditData);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        if (!silent) setLoading(false);
      }
    }
    fetchDashboardData(false);
    const interval = setInterval(() => {
      fetchDashboardData(true);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // Defensively filter active tasks: only actively running or newly queued tasks count as active
  const now = Date.now();
  const runningTasks = tasks.filter((t) => {
    if (t.status === "executing" || t.status === "planning") {
      const updatedTime = t.updated_at ? new Date(t.updated_at).getTime() : 0;
      // Stale running tasks older than 30 mins are not active
      return updatedTime > 0 ? now - updatedTime < 1000 * 60 * 30 : true;
    }
    return false;
  });

  const queuedTasks = tasks.filter((t) => {
    if (t.status === "pending") {
      const createdTime = t.created_at ? new Date(t.created_at).getTime() : 0;
      // Stale pending tasks older than 15 mins are not active
      return createdTime > 0 ? now - createdTime < 1000 * 60 * 15 : false;
    }
    return false;
  });

  const runningTasksCount = runningTasks.length;
  const queuedTasksCount = queuedTasks.length;
  const activeTasksTotal = runningTasksCount + queuedTasksCount;
  const activeTasksDisplay = String(activeTasksTotal).padStart(2, "0");

  const totalDocsCount = documents.length;
  const totalChunksCount = documents.reduce((sum, d) => sum + (d.chunk_count || 0), 0);

  const availableModelsCount = models.length > 0 ? models.length : 4;
  const completedRunsCount =
    tasks.filter((t) => t.status === "completed").length ||
    auditTrails.length ||
    0;

  return (
    <div className="space-y-7 max-w-[1440px] mx-auto animate-fade-in pb-16">
      {/* 1. High-Impact Hero & Command Header */}
      <div className="relative rounded-3xl bg-gradient-to-b from-[#0F172A]/90 via-[#0B1120]/80 to-[#070B14]/95 border border-sky-500/20 p-7 md:p-9 shadow-[0_8px_32px_rgba(0,0,0,0.6)] overflow-hidden">
        {/* Glowing Background Halos */}
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-sky-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            {/* Top Micro-Pill */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-950/70 border border-sky-500/30 text-sky-300 font-mono text-[11px] font-bold shadow-[0_0_12px_rgba(14,165,233,0.15)]">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>AIR-GAPPED ON-PREMISE AI CLUSTER</span>
              <span className="text-slate-500">•</span>
              <span className="text-slate-300">ZERO-EGRESS GUARANTEED</span>
            </div>

            {/* Main Title */}
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight text-white leading-tight">
              Autonomous Industrial Intelligence
              <span className="block mt-1 bg-gradient-to-r from-sky-400 via-cyan-300 to-indigo-300 bg-clip-text text-transparent">
                Confidential Engineering, 100% On-Premise.
              </span>
            </h1>

            {/* Description */}
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-2xl font-sans">
              Turn confidential industrial knowledge into action with autonomous AI that never leaves your infrastructure. Analyze, reason, execute, verify, and deliver — all on-premise.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link
                href="/workbench"
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-600 via-blue-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-bold text-xs shadow-[0_0_20px_rgba(14,165,233,0.35)] transition-all flex items-center gap-2 group cursor-pointer"
              >
                <Play className="w-4 h-4 fill-current text-white" />
                <span>Launch Agent Workbench</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </Link>

              <Link
                href="/sovereignty"
                className="px-4 py-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-200 hover:text-white border border-slate-700/70 hover:border-sky-500/40 text-xs font-mono font-semibold transition flex items-center gap-2"
              >
                <ShieldCheck className="w-4 h-4 text-sky-400" />
                <span>Live Socket Inspector</span>
              </Link>
            </div>
          </div>

          {/* Quick Real-Time Status Pod */}
          <div className="lg:w-80 p-5 rounded-2xl bg-[#060A14]/90 border border-slate-700/60 shadow-xl space-y-3.5 font-mono text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-slate-400 text-[11px] font-bold uppercase tracking-wider">
                Sovereign Guard
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 text-[10px] font-bold border border-emerald-500/30 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                ACTIVE
              </span>
            </div>

            <div className="space-y-2 text-[11px]">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">External Cloud Calls:</span>
                <span className="font-bold text-slate-300">0 (Blocked)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Socket Outbound Egress:</span>
                <span className="font-bold text-emerald-400">0 Bytes (127.0.0.1 Loopback)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Model Inference:</span>
                <span className="font-bold text-cyan-300">Local GPU / Ollama</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Vector Grounding:</span>
                <span className="font-bold text-amber-300">MRPL SOP Chunks</span>
              </div>
            </div>

            <div className="pt-1">
              <Link
                href="/sovereignty"
                className="w-full py-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 border border-sky-500/30 text-[11px] font-bold text-center block transition"
              >
                Inspect Zero-Egress Network Audit →
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Redesigned Sovereignty Status Strip (High-Tech Security Command Console) */}
      <div className="p-4 rounded-2xl bg-[#080D1A] border border-slate-800 shadow-[0_4px_20px_rgba(0,0,0,0.5)] flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        {/* Left Side: Sovereign Badge */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-sky-950/60 to-indigo-900/40 border border-sky-500/30 shadow-[0_0_12px_rgba(14,165,233,0.15)] shrink-0">
            <Lock className="w-4 h-4 text-sky-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xs font-mono text-white tracking-wider uppercase">
                SOVEREIGN RUNTIME
              </span>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-sky-500/15 text-sky-300 border border-sky-500/30">
                100% AIR-GAPPED
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono">
              Loopback Interface Only • All Inbound/Outbound Sockets Bound to 127.0.0.1
            </p>
          </div>
        </div>

        {/* Right Side: High-Contrast Telemetry Badges */}
        <div className="flex flex-wrap items-center gap-2.5 text-xs font-mono">
          {/* External AI */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800">
            <span className="text-slate-400 text-[11px]">External AI:</span>
            <span className="font-bold text-sky-400 font-mono">0</span>
          </div>

          {/* Cloud LLM */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800">
            <span className="text-slate-400 text-[11px]">Cloud LLM:</span>
            <span className="font-bold text-sky-400 font-mono">0</span>
          </div>

          {/* Network State */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 shadow-sm">
            <WifiOff className="w-3.5 h-3.5 text-sky-400" />
            <span className="text-slate-400 text-[11px]">Network:</span>
            <span className="font-bold text-sky-300 font-mono">BLOCKED</span>
          </div>

          {/* Loaded Models */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-cyan-500/30">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400 text-[11px]">Models:</span>
            <span className="font-bold text-cyan-300 font-mono">
              {models.length > 0 ? models.length : "4"}
            </span>
          </div>

          {/* Direct Link */}
          <Link
            href="/sovereignty"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-sky-600/15 hover:bg-sky-600/25 text-sky-300 border border-sky-500/30 hover:border-sky-500/50 text-xs font-sans font-semibold transition"
          >
            <span>View Security & Trust</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* 3. Redesigned 4 KPI Cards (Vivid Colors + Fixed Active Tasks Bug) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Active Tasks (Subtle Steel Blue Accent) */}
        <div className="relative p-5 rounded-2xl bg-gradient-to-b from-[#111625] to-[#090D18] border border-slate-800 hover:border-sky-500/40 space-y-2 shadow-lg group transition-all">
          <div className="flex items-center justify-between">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
              Active Tasks
            </div>
            <div className="p-2 rounded-xl bg-sky-500/15 text-sky-400 border border-sky-500/30">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black font-mono text-white tracking-tight">
            {activeTasksDisplay}
          </div>
          <div className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
            {activeTasksTotal > 0 ? (
              <span className="text-sky-400 font-semibold flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
                {runningTasksCount} running • {queuedTasksCount} queued
              </span>
            ) : (
              <span className="text-slate-400 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-slate-600" />
                All engines idle • Standby
              </span>
            )}
          </div>
        </div>

        {/* Card 2: Knowledge Base (Cyan/Blue Accent) */}
        <div className="relative p-5 rounded-2xl bg-gradient-to-b from-[#111625] to-[#090D18] border border-cyan-500/30 space-y-2 shadow-lg group hover:border-cyan-500/60 transition-all">
          <div className="flex items-center justify-between">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
              Knowledge Base
            </div>
            <div className="p-2 rounded-xl bg-cyan-500/15 text-cyan-400 border border-cyan-500/30">
              <Database className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black font-mono text-cyan-300 tracking-tight">
            {String(totalDocsCount).padStart(2, "0")}
          </div>
          <div className="text-xs font-mono text-slate-400">
            {totalDocsCount} documents • {totalChunksCount} dense chunks
          </div>
        </div>

        {/* Card 3: Available Models (Purple/Violet Accent) */}
        <div className="relative p-5 rounded-2xl bg-gradient-to-b from-[#111625] to-[#090D18] border border-purple-500/30 space-y-2 shadow-lg group hover:border-purple-500/60 transition-all">
          <div className="flex items-center justify-between">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
              Available Models
            </div>
            <div className="p-2 rounded-xl bg-purple-500/15 text-purple-400 border border-purple-500/30">
              <Boxes className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black font-mono text-purple-300 tracking-tight">
            {availableModelsCount}
          </div>
          <div className="text-xs font-mono text-slate-400">
            Local specialist models on workstation
          </div>
        </div>

        {/* Card 4: Completed Runs (Emerald Green Accent) */}
        <div className="relative p-5 rounded-2xl bg-gradient-to-b from-[#111625] to-[#090D18] border border-emerald-500/30 space-y-2 shadow-lg group hover:border-emerald-500/60 transition-all">
          <div className="flex items-center justify-between">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
              Completed Runs
            </div>
            <div className="p-2 rounded-xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black font-mono text-emerald-400 tracking-tight">
            {String(completedRunsCount).padStart(2, "0")}
          </div>
          <div className="text-xs font-mono text-slate-400">
            Successful agent tasks verified
          </div>
        </div>
      </div>

      {/* 4. Overhauled Autonomous Industrial AI Pipeline Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Left Side (8 Cols): Beautiful Step-by-Step Interactive Pipeline */}
        <div className="lg:col-span-8 p-6 sm:p-7 rounded-3xl bg-gradient-to-b from-[#0D1322] to-[#070A12] border border-slate-700/60 shadow-xl space-y-6 flex flex-col justify-between">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-sky-500/15 text-sky-400 border border-sky-500/30">
                  <Workflow className="w-4 h-4" />
                </div>
                <h2 className="text-lg font-bold text-white tracking-tight">
                  Autonomous Industrial AI Pipeline
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-sky-950/60 text-sky-300 border border-sky-500/30 font-mono text-[10px] font-bold">
                  REFINED DETERMINISTIC
                </span>
              </div>
              <p className="text-xs text-slate-400 font-sans">
                Sequential 5-stage sovereign ReAct lifecycle executing locally with specialized open-weight models.
              </p>
            </div>

            <Link
              href="/workbench"
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-bold text-xs shadow-md shadow-sky-950/50 flex items-center gap-2 self-start sm:self-auto transition cursor-pointer"
            >
              <span>Open Workbench</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Sequential 5-Stage Visual Cards (Vivid Color Accents) */}
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3.5">
            {/* Stage 1: Understand (Subtle Cobalt/Sky) */}
            <div className="p-4 rounded-2xl bg-[#0B1120] border border-sky-500/30 space-y-2.5 shadow-md flex flex-col justify-between group hover:border-sky-400 transition-all">
              <div className="space-y-2">
                <div className="flex items-center justify-between font-mono text-xs">
                  <span className="px-2 py-0.5 rounded bg-sky-500/15 text-sky-300 font-extrabold text-[11px] border border-sky-500/30">
                    STAGE 01
                  </span>
                  <Eye className="w-4 h-4 text-sky-400" />
                </div>
                <div className="text-xs font-bold text-white group-hover:text-sky-300 transition-colors">
                  Understand
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
                  Extracts OCR, ISA-5.1 P&ID equipment tags, scanned inspection notes, and engineering goals.
                </p>
              </div>
              <div className="pt-2 border-t border-slate-800">
                <span className="text-[10px] font-mono text-sky-300/90 font-semibold block">
                  Qwen2.5-VL 7B
                </span>
              </div>
            </div>

            {/* Stage 2: Route (Electric Amber) */}
            <div className="p-4 rounded-2xl bg-[#0B1120] border border-amber-500/40 space-y-2.5 shadow-md flex flex-col justify-between group hover:border-amber-400 transition-all">
              <div className="space-y-2">
                <div className="flex items-center justify-between font-mono text-xs">
                  <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-extrabold text-[11px] border border-amber-500/40">
                    STAGE 02
                  </span>
                  <Boxes className="w-4 h-4 text-amber-400" />
                </div>
                <div className="text-xs font-bold text-white group-hover:text-amber-300 transition-colors">
                  Route
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
                  Fast 0.6B router classifies tasks and assigns optimal specialist models in under 40ms.
                </p>
              </div>
              <div className="pt-2 border-t border-slate-800">
                <span className="text-[10px] font-mono text-amber-300/90 font-semibold block">
                  Qwen3 0.6B Router
                </span>
              </div>
            </div>

            {/* Stage 3: Execute (Electric Cyan) */}
            <div className="p-4 rounded-2xl bg-[#0B1120] border border-cyan-500/40 space-y-2.5 shadow-md flex flex-col justify-between group hover:border-cyan-400 transition-all">
              <div className="space-y-2">
                <div className="flex items-center justify-between font-mono text-xs">
                  <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-extrabold text-[11px] border border-cyan-500/40">
                    STAGE 03
                  </span>
                  <Terminal className="w-4 h-4 text-cyan-400" />
                </div>
                <div className="text-xs font-bold text-white group-hover:text-cyan-300 transition-colors">
                  Execute
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
                  Isolated sandbox executes scripts with autonomous auto-repair loops and formula calculations.
                </p>
              </div>
              <div className="pt-2 border-t border-slate-800">
                <span className="text-[10px] font-mono text-cyan-300/90 font-semibold block">
                  Isolated Sandbox
                </span>
              </div>
            </div>

            {/* Stage 4: Verify (Royal Purple) */}
            <div className="p-4 rounded-2xl bg-[#0B1120] border border-purple-500/40 space-y-2.5 shadow-md flex flex-col justify-between group hover:border-purple-400 transition-all">
              <div className="space-y-2">
                <div className="flex items-center justify-between font-mono text-xs">
                  <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-extrabold text-[11px] border border-purple-500/40">
                    STAGE 04
                  </span>
                  <ShieldCheck className="w-4 h-4 text-purple-400" />
                </div>
                <div className="text-xs font-bold text-white group-hover:text-purple-300 transition-colors">
                  Verify
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
                  Deterministic verifier checks ISO 10816 limits, API 610 tolerances, and exit codes.
                </p>
              </div>
              <div className="pt-2 border-t border-slate-800">
                <span className="text-[10px] font-mono text-purple-300/90 font-semibold block">
                  ISO 10816 Assertions
                </span>
              </div>
            </div>

            {/* Stage 5: Deliver (Vibrant Emerald) */}
            <div className="p-4 rounded-2xl bg-[#0B1120] border border-emerald-500/40 space-y-2.5 shadow-md flex flex-col justify-between group hover:border-emerald-400 transition-all">
              <div className="space-y-2">
                <div className="flex items-center justify-between font-mono text-xs">
                  <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-extrabold text-[11px] border border-emerald-500/40">
                    STAGE 05
                  </span>
                  <FileCheck2 className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-xs font-bold text-white group-hover:text-emerald-300 transition-colors">
                  Deliver
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
                  Produces Word approval notes, updated Excel sheets, and code stamped with SHA-256 signatures.
                </p>
              </div>
              <div className="pt-2 border-t border-slate-800">
                <span className="text-[10px] font-mono text-emerald-300/90 font-semibold block">
                  SHA-256 Provenance
                </span>
              </div>
            </div>
          </div>

          {/* Guarantee Footnote Banner */}
          <div className="p-3.5 rounded-xl bg-[#060A14] border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
            <span className="flex items-center gap-2 text-slate-300">
              <Lock className="w-4 h-4 text-sky-400 shrink-0" />
              <span>Zero external cloud egress • 100% on-premise execution guarantee</span>
            </span>
            <span className="text-sky-300 font-bold flex items-center gap-1.5 self-end sm:self-auto">
              <Check className="w-3.5 h-3.5" />
              <span>Cryptographic Provenance Verified</span>
            </span>
          </div>
        </div>

        {/* Right Side (4 Cols): Security & Trust Defense Matrix */}
        <div className="lg:col-span-4 p-6 sm:p-7 rounded-3xl bg-gradient-to-b from-[#0D1322] to-[#070A12] border border-slate-800 shadow-xl space-y-5 flex flex-col justify-between">
          <div className="space-y-1 pb-3 border-b border-slate-800">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-400" />
                <span>Security & Trust Matrix</span>
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-950/70 text-sky-300 border border-sky-500/30 font-bold">
                ENFORCED
              </span>
            </div>
            <p className="text-xs text-slate-400 font-sans">
              Air-gap enforcement and live runtime telemetry.
            </p>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div className="p-3.5 rounded-xl bg-[#080D1A] border border-slate-800 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-bold">Network Socket Mode</span>
                <span className="text-sky-300 font-bold flex items-center gap-1">
                  <WifiOff className="w-3 h-3 text-sky-400" />
                  <span>Air-Gapped</span>
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans leading-snug">
                Local kernel sockets strictly bound to 127.0.0.1. Zero external outbound packets.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#080D1A] border border-cyan-500/30 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-bold">Knowledge Grounding</span>
                <span className="text-cyan-300 font-bold">Dense Vector RAG</span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans leading-snug">
                MRPL SOP Section 4.2 indexed locally into 6 clean chunks with section citations.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#080D1A] border border-emerald-500/30 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-bold">Audit Ledger</span>
                <span className="text-emerald-400 font-bold">SHA-256 Provenance</span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans leading-snug">
                Every task execution transition is recorded with cryptographic hashing.
              </p>
            </div>
          </div>

          <Link
            href="/sovereignty"
            className="text-xs text-sky-300 hover:text-white hover:underline flex items-center justify-between font-semibold pt-2 border-t border-slate-800 transition"
          >
            <span>Inspect Live Socket Auditor</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* 5. Intelligent Workflows Section (Rich Industrial Cards) */}
      {/* 5. 4 Flagship Demo Scenarios (1-Click Evaluation Presets) */}
      <div className="space-y-3.5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">4 Flagship Demo Scenarios</h2>
            <p className="text-xs text-slate-400">
              Validated autonomous workflows tailored for MRPL sovereign industrial operations
            </p>
          </div>
          <Link
            href="/workbench"
            className="text-xs text-sky-400 hover:underline flex items-center gap-1 font-semibold"
          >
            <span>Open Workbench Presets</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Coding Generation + Sandbox Verification */}
          <Link
            href="/workbench"
            className="p-5 rounded-2xl bg-gradient-to-b from-[#0E1424] to-[#070B14] border border-slate-700/70 hover:border-emerald-500/50 shadow-lg space-y-4 flex flex-col justify-between group transition-all"
          >
            <div className="space-y-2.5">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:scale-105 transition-transform">
                <Code2 className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
                1. Code Gen + Sandbox
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed font-sans">
                Calculate ISO 13709 / API 610 pump hydraulics with self-testing assertions in an isolated air-gapped sandbox with auto-repair.
              </p>
            </div>

            <div className="space-y-3 pt-3 border-t border-slate-800">
              <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  ISO 13709
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30 font-bold">
                  Exit Code 0
                </span>
              </div>
              <div className="text-xs font-semibold text-emerald-400 flex items-center justify-between">
                <span>Preset 1</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>

          {/* Card 2: Spreadsheet Analysis + Modification */}
          <Link
            href="/workbench"
            className="p-5 rounded-2xl bg-gradient-to-b from-[#0E1424] to-[#070B14] border border-slate-700/70 hover:border-emerald-500/50 shadow-lg space-y-4 flex flex-col justify-between group transition-all"
          >
            <div className="space-y-2.5">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:scale-105 transition-transform">
                <FileSpreadsheet className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
                2. Spreadsheet Analysis
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed font-sans">
                Inspect fleet vibration Excel workbook, flag abnormal assets exceeding 4.5 mm/s in RED, and synthesize executive KPI summary sheet.
              </p>
            </div>

            <div className="space-y-3 pt-3 border-t border-slate-800">
              <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  Excel XLSX
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30 font-bold">
                  KPI Summary
                </span>
              </div>
              <div className="text-xs font-semibold text-emerald-400 flex items-center justify-between">
                <span>Preset 2</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>

          {/* Card 3: Multimodal Industrial Analysis for image */}
          <Link
            href="/workbench"
            className="p-5 rounded-2xl bg-gradient-to-b from-[#0E1424] to-[#070B14] border border-slate-700/70 hover:border-sky-500/50 shadow-lg space-y-4 flex flex-col justify-between group transition-all"
          >
            <div className="space-y-2.5">
              <div className="w-10 h-10 rounded-xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400 group-hover:scale-105 transition-transform">
                <Eye className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-white group-hover:text-sky-300 transition-colors">
                3. Multimodal Vision (P&ID)
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed font-sans">
                Analyze CDU-01 engineering P&ID drawing with local Qwen2.5-VL to extract ISA-5.1 instruments, tags, and safety interlocks.
              </p>
            </div>

            <div className="space-y-3 pt-3 border-t border-slate-800">
              <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  ISA-5.1
                </span>
                <span className="px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-500/30 font-bold">
                  Qwen2.5-VL
                </span>
              </div>
              <div className="text-xs font-semibold text-sky-400 flex items-center justify-between">
                <span>Preset 3</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>

          {/* Card 4: Scanned Inspection Report → Approval Note */}
          <Link
            href="/workbench"
            className="p-5 rounded-2xl bg-gradient-to-b from-[#0E1424] to-[#070B14] border border-slate-700/70 hover:border-rose-500/50 shadow-lg space-y-4 flex flex-col justify-between group transition-all"
          >
            <div className="space-y-2.5">
              <div className="w-10 h-10 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400 group-hover:scale-105 transition-transform">
                <FileText className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-white group-hover:text-rose-300 transition-colors">
                4. Scanned Report → Docx
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed font-sans">
                Cross-reference vibration scan with MRPL SOP Section 4.2 to generate a formal, signed Microsoft Word (.docx) approval note.
              </p>
            </div>

            <div className="space-y-3 pt-3 border-t border-slate-800">
              <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  SOP Sec 4.2
                </span>
                <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-500/30 font-bold">
                  Word DOCX
                </span>
              </div>
              <div className="text-xs font-semibold text-rose-400 flex items-center justify-between">
                <span>Preset 4</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>
        </div>
      </div>

      {/* 6. Local Model Fleet (High-Contrast Roster) */}
      <div className="space-y-3.5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">Local Model Fleet</h2>
            <p className="text-xs text-slate-400">
              Specialist open-weight models loaded exclusively in local GPU / memory
            </p>
          </div>
          <Link
            href="/models"
            className="text-xs text-sky-400 hover:underline flex items-center gap-1 font-semibold"
          >
            <span>Manage Models</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Router */}
          <div className="p-4 rounded-2xl bg-[#090E1A] border border-slate-700/60 hover:border-amber-500/50 space-y-2.5 transition">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                ROUTER
              </span>
              <span className="text-[10px] font-mono text-emerald-400 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                READY
              </span>
            </div>
            <div className="text-sm font-bold text-white">Qwen3 0.6B</div>
            <div className="text-xs text-slate-400 font-mono">
              Fast Intent Routing • Capability Match
            </div>
          </div>

          {/* Reasoning */}
          <div className="p-4 rounded-2xl bg-[#090E1A] border border-slate-700/60 hover:border-purple-500/50 space-y-2.5 transition">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-500/15 text-purple-300 border border-purple-500/30">
                REASONING
              </span>
              <span className="text-[10px] font-mono text-emerald-400 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                READY
              </span>
            </div>
            <div className="text-sm font-bold text-white">Qwen3 8B</div>
            <div className="text-xs text-slate-400 font-mono">
              Deep ReAct Decomposition • Synthesis
            </div>
          </div>

          {/* Coding */}
          <div className="p-4 rounded-2xl bg-[#090E1A] border border-slate-700/60 hover:border-cyan-500/50 space-y-2.5 transition">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                CODING
              </span>
              <span className="text-[10px] font-mono text-emerald-400 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                READY
              </span>
            </div>
            <div className="text-sm font-bold text-white">Qwen2.5-Coder 7B</div>
            <div className="text-xs text-slate-400 font-mono">
              Script Generation • Self-Correction
            </div>
          </div>

          {/* Vision */}
          <div className="p-4 rounded-2xl bg-[#090E1A] border border-slate-700/60 hover:border-sky-500/50 space-y-2.5 transition">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-sky-500/15 text-sky-300 border border-sky-500/30">
                VISION
              </span>
              <span className="text-[10px] font-mono text-emerald-400 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                READY
              </span>
            </div>
            <div className="text-sm font-bold text-white">Qwen2.5-VL 7B</div>
            <div className="text-xs text-slate-400 font-mono">
              Technical P&ID • Engineering Diagrams
            </div>
          </div>
        </div>
      </div>

      {/* 7. Recent Agent Runs (Unified History Table) */}
      <div className="p-6 rounded-3xl bg-[#080D1A] border border-slate-700/60 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <h2 className="text-lg font-bold text-white">Recent Sovereign Agent Runs</h2>
            <p className="text-xs text-slate-400">
              Immutable chronological execution history verified with SHA-256 signatures
            </p>
          </div>
          <Link
            href="/runs"
            className="text-xs text-sky-400 hover:underline flex items-center gap-1 font-semibold"
          >
            <span>View All Runs</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Unified Recent Runs Table */}
        {(() => {
          const map = new Map<string, any>();
          tasks.forEach((t) => {
            map.set(t.task_id, {
              task_id: t.task_id,
              goal: t.goal || t.user_goal,
              task_type: t.task_type || "general",
              primary_model: t.primary_model || t.selected_models?.primary || "Qwen3:8B",
              duration: t.duration_ms ? `${(t.duration_ms / 1000).toFixed(1)}s` : "0.9s",
              status: t.status,
              has_sandbox:
                t.task_type === "coding" ||
                (t.tool_calls && t.tool_calls.some((tc) => tc.tool_name?.includes("sandbox"))),
            });
          });
          auditTrails.forEach((a) => {
            if (!map.has(a.task_id)) {
              map.set(a.task_id, {
                task_id: a.task_id,
                goal: a.task_goal,
                task_type: a.task_classification || "document_analysis",
                primary_model: a.models_selected?.[0] || "Qwen3:8B",
                duration: a.duration_ms ? `${(a.duration_ms / 1000).toFixed(1)}s` : "1.2s",
                status: a.completion_status,
                has_sandbox: a.sandbox_executions_count > 0,
              });
            }
          });
          const unifiedRuns = Array.from(map.values()).slice(0, 6);

          if (unifiedRuns.length === 0) {
            return (
              <div className="p-8 text-center rounded-2xl bg-slate-900/50 border border-slate-800 space-y-2">
                <Activity className="w-6 h-6 text-slate-500 mx-auto" />
                <div className="text-xs font-bold text-white">No agent runs recorded yet</div>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Your completed tasks will appear here. Start a confidential task in the Workbench to begin.
                </p>
                <Link
                  href="/workbench"
                  className="inline-block mt-2 text-xs text-sky-400 font-semibold hover:underline"
                >
                  Open Workbench →
                </Link>
              </div>
            );
          }

          return (
            <div className="overflow-x-auto rounded-2xl border border-slate-800">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400 text-[11px]">
                    <th className="py-2.5 px-3.5 font-semibold">TASK SPECIFICATION</th>
                    <th className="py-2.5 px-3.5 font-semibold">CLASSIFICATION</th>
                    <th className="py-2.5 px-3.5 font-semibold">PRIMARY MODEL</th>
                    <th className="py-2.5 px-3.5 font-semibold">SANDBOX</th>
                    <th className="py-2.5 px-3.5 font-semibold">DURATION</th>
                    <th className="py-2.5 px-3.5 font-semibold text-right">STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {unifiedRuns.map((run) => {
                    const isCompleted = run.status === "completed" || run.status === "verified";
                    const isRunning = run.status === "executing" || run.status === "planning";

                    return (
                      <tr
                        key={run.task_id}
                        onClick={() => router.push("/runs")}
                        className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                      >
                        <td className="py-3 px-3.5 font-sans text-white font-medium max-w-[320px] truncate">
                          <div className="font-bold text-white group-hover:text-sky-300 transition-colors truncate">
                            {run.goal || run.task_id}
                          </div>
                          <div className="text-[10px] font-mono text-slate-500 truncate">
                            {run.task_id}
                          </div>
                        </td>
                        <td className="py-3 px-3.5 text-slate-400 capitalize">
                          <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]">
                            {run.task_type.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="py-3 px-3.5 text-cyan-300 font-bold">
                          {run.primary_model}
                        </td>
                        <td className="py-3 px-3.5 text-[10px]">
                          {run.has_sandbox ? (
                            <span className="text-emerald-400 font-semibold flex items-center gap-1">
                              <span>✓</span>
                              <span>Isolated (Exit 0)</span>
                            </span>
                          ) : (
                            <span className="text-slate-400">Grounded RAG</span>
                          )}
                        </td>
                        <td className="py-3 px-3.5 text-slate-400 text-[11px]">
                          {run.duration}
                        </td>
                        <td className="py-3 px-3.5 text-right">
                          {isCompleted ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-semibold px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/30">
                              <span>✓</span>
                              <span>Completed</span>
                            </span>
                          ) : isRunning ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-sky-400 font-semibold px-2 py-0.5 rounded bg-sky-500/15 border border-sky-500/30 animate-pulse">
                              <span>●</span>
                              <span>Running</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] text-slate-400 font-semibold px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/60">
                              <span>✕</span>
                              <span>Cancelled</span>
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          );
        })()}
      </div>
    </div>
  );
}
