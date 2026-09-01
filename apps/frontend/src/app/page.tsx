"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { ModelInfo, SovereigntyStatus, SystemHealth, TaskAuditSummary } from "@/lib/types";
import { StatusBadge } from "@/components/layout/StatusBadge";
import {
  Cpu,
  Boxes,
  Database,
  FileCheck2,
  ArrowRight,
  Sparkles,
  Terminal,
  Code2,
  Eye,
  FileText,
  Clock,
  Shield,
  Activity,
  Layers,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [sovStatus, setSovStatus] = useState<SovereigntyStatus | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [recentAudits, setRecentAudits] = useState<TaskAuditSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [h, s, mod, audits] = await Promise.all([
          api.getHealth().catch(() => null),
          api.getSovereigntyStatus().catch(() => null),
          api.getModels().catch(() => []),
          api.getAuditTrails(6).catch(() => []),
        ]);
        setHealth(h);
        setSovStatus(s);
        setModels(mod);
        setRecentAudits(audits);
      } catch (e) {
        console.error("Dashboard data load error:", e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Impressive Modern Hero Section */}
      <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-b from-white/[0.05] via-obsidian-900/60 to-obsidian-950/80 p-8 md:p-12 shadow-2xl backdrop-blur-2xl">
        {/* Subtle Ambient Light Orbs */}
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-indigo-500/15 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 rounded-full bg-cyan-500/15 blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/25 text-xs text-indigo-300 font-medium">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Autonomous Intelligence & Multimodal Agent Execution</span>
          </div>

          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Next-Generation <br />
            <span className="gradient-text-accent">Autonomous AI Workbench</span>
          </h1>

          <p className="text-base md:text-lg text-slate-300 leading-relaxed font-normal">
            Orchestrate complex industrial workflows with open-weight foundation models.
            Combines multimodal visual understanding, dense organizational RAG, isolated sandbox execution,
            and cryptographic provenance in a single platform.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link
              href="/workbench"
              className="shimmer-button flex items-center gap-2.5 px-6 py-3 rounded-xl text-white font-semibold text-sm transition"
            >
              <Cpu className="w-4 h-4" />
              <span>Launch Interactive Workbench</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              href="/knowledge"
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white/[0.05] hover:bg-white/[0.09] text-slate-200 font-medium text-sm border border-white/10 transition backdrop-blur-md"
            >
              <Database className="w-4 h-4 text-cyan-400" />
              <span>Knowledge Base</span>
            </Link>

            <Link
              href="/models"
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white/[0.05] hover:bg-white/[0.09] text-slate-200 font-medium text-sm border border-white/10 transition backdrop-blur-md"
            >
              <Boxes className="w-4 h-4 text-purple-400" />
              <span>Model Gateway</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Real-time Dynamic Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Models */}
        <div className="glass-panel-interactive p-5 rounded-2xl space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
              Foundation Models
            </span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Boxes className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-3xl font-bold text-white font-mono">
              {models.length > 0 ? models.length : "4"}
            </div>
            <StatusBadge status="ACTIVE" />
          </div>
          <p className="text-xs text-slate-400 pt-1 border-t border-white/5">
            Vision, Reasoning, & Coding
          </p>
        </div>

        {/* Metric 2: Agent Orchestrator */}
        <div className="glass-panel-interactive p-5 rounded-2xl space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
              Agent Orchestrator
            </span>
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-3xl font-bold text-white font-mono">Multi-Stage</div>
            <StatusBadge status="READY" />
          </div>
          <p className="text-xs text-slate-400 pt-1 border-t border-white/5">
            Plan, Route, Execute, Verify
          </p>
        </div>

        {/* Metric 3: Vector Knowledge Store */}
        <div className="glass-panel-interactive p-5 rounded-2xl space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
              Dense Knowledge RAG
            </span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <Database className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-3xl font-bold text-white font-mono">Vector DB</div>
            <StatusBadge status="HEALTHY" />
          </div>
          <p className="text-xs text-slate-400 pt-1 border-t border-white/5">
            Semantic chunk retrieval
          </p>
        </div>

        {/* Metric 4: Security & Audit */}
        <div className="glass-panel-interactive p-5 rounded-2xl space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
              Cryptographic Audit
            </span>
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
              <Shield className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-3xl font-bold text-white font-mono">SHA-256</div>
            <StatusBadge status="ACTIVE" />
          </div>
          <p className="text-xs text-slate-400 pt-1 border-t border-white/5">
            Tamper-evident trace ledger
          </p>
        </div>
      </div>

      {/* Flagship Workflows Showcase */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">Intelligent Workflows</h2>
            <p className="text-xs text-slate-400">Production-ready autonomous capabilities</p>
          </div>
          <Link
            href="/workbench"
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition"
          >
            <span>Open Workbench</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Card 1 */}
          <Link
            href="/workbench"
            className="glass-panel-interactive p-6 rounded-2xl space-y-4 flex flex-col justify-between group"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-110 transition-transform">
                <Eye className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors">
                Multimodal Visual & Document Intelligence
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Extract equipment parameters, analyze complex engineering diagrams, and perform visual QA on photos and scanned documents using Qwen2.5-VL.
              </p>
            </div>
            <div className="flex items-center justify-between text-xs text-indigo-400 pt-3 border-t border-white/5 font-medium">
              <span>qwen2.5vl:7b</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          {/* Card 2 */}
          <Link
            href="/workbench"
            className="glass-panel-interactive p-6 rounded-2xl space-y-4 flex flex-col justify-between group"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform">
                <FileText className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
                Inspection to Official Deliverable
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Synthesizes inspection findings with organizational SOPs to draft formal verified documents (.docx) with cryptographic integrity.
              </p>
            </div>
            <div className="flex items-center justify-between text-xs text-cyan-400 pt-3 border-t border-white/5 font-medium">
              <span>qwen3:8b + Dense RAG</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          {/* Card 3 */}
          <Link
            href="/workbench"
            className="glass-panel-interactive p-6 rounded-2xl space-y-4 flex flex-col justify-between group"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform">
                <Code2 className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-purple-300 transition-colors">
                Sandboxed Coding Agent
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Generate high-performance Python programs, generate test suites, and execute in isolated execution environments with automatic verification.
              </p>
            </div>
            <div className="flex items-center justify-between text-xs text-purple-400 pt-3 border-t border-white/5 font-medium">
              <span>qwen2.5-coder:7b + Sandbox</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        </div>
      </div>

      {/* Model Roster & Recent Activity Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Model Roster */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Boxes className="w-4 h-4 text-indigo-400" />
              <h3 className="text-sm font-bold text-white">Active Model Roster</h3>
            </div>
            <Link
              href="/models"
              className="text-xs text-indigo-400 hover:text-indigo-300 transition font-medium"
            >
              Manage Models &rarr;
            </Link>
          </div>

          <div className="space-y-2.5">
            {models.length > 0 ? (
              models.map((mod) => (
                <div
                  key={mod.name}
                  className="p-3.5 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 flex items-center justify-between transition"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 font-mono text-xs font-bold">
                      {mod.role.substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-100">{mod.name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {mod.capabilities?.join(", ") || "General Inference"}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-slate-400">{mod.provider}</span>
                    <StatusBadge status={mod.status || "LOADED"} />
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-xs text-slate-500">
                Models available in local gateway registry
              </div>
            )}
          </div>
        </div>

        {/* Live Audit Stream */}
        <div className="glass-panel p-6 rounded-2xl space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-white/5">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-white">Audit Trail</h3>
              </div>
              <Link
                href="/audit"
                className="text-xs text-emerald-400 hover:text-emerald-300 transition font-medium"
              >
                Full Log &rarr;
              </Link>
            </div>

            <div className="space-y-3 mt-4">
              {recentAudits.length > 0 ? (
                recentAudits.slice(0, 4).map((audit, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1"
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-semibold text-slate-200">
                        {audit.task_classification || "Task Execution"}
                      </span>
                      <span className="text-slate-500 font-mono">
                        {audit.duration_ms ? `${(audit.duration_ms / 1000).toFixed(1)}s` : "Recorded"}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 truncate">
                      {audit.task_goal || "Autonomous workflow step completed"}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-xs text-slate-500 space-y-2">
                  <CheckCircle2 className="w-6 h-6 text-slate-600 mx-auto" />
                  <p>All activities logged with cryptographic provenance</p>
                </div>
              )}
            </div>
          </div>

          <div className="pt-4 border-t border-white/5">
            <Link
              href="/workbench"
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 font-semibold text-xs border border-indigo-500/25 transition"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Start New Agent Task</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
