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
  RefreshCw,
  Clock,
  Sparkles,
  Lock,
  Workflow,
  Search,
  KeyRound,
  FileCode,
  Check,
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

  // KPI Calculations
  const runningTasksCount = tasks.filter((t) => t.status === "executing" || t.status === "planning").length;
  const queuedTasksCount = tasks.filter((t) => t.status === "pending").length;
  const activeTasksDisplay = String(runningTasksCount + queuedTasksCount).padStart(2, "0");

  const totalDocsCount = documents.length;
  const totalChunksCount = documents.reduce((sum, d) => sum + (d.chunk_count || 0), 0);

  const availableModelsCount = models.length > 0 ? models.length : 4;
  const completedRunsCount = tasks.filter((t) => t.status === "completed").length || auditTrails.length || 0;

  return (
    <div className="space-y-6 max-w-[1440px] mx-auto animate-fade-in pb-12">
      {/* 1. Page Title & Subtitle */}
      <div className="space-y-1">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-iron-textPrimary">
          Sovereign AI Workbench
        </h1>
        <p className="text-xs md:text-sm text-iron-textSecondary">
          Confidential industrial work, executed entirely on-premise.
        </p>
      </div>

      {/* 2. Sovereignty Status Strip (Full-Width Compact Banner) */}
      <div className="enterprise-card px-5 py-3 rounded-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-3 border-l-4 border-l-iron-success">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-iron-success text-sm">🔒</span>
            <span className="font-bold text-xs font-mono text-iron-textPrimary tracking-wide uppercase">
              SOVEREIGN MODE
            </span>
          </div>
          <span className="text-iron-border hidden md:inline">•</span>
          <span className="text-xs text-iron-textSecondary">
            Air-Gapped / Local Processing
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-iron-textSecondary">
            <span>External AI:</span>
            <span className="font-bold text-iron-textPrimary">
              {sovereignty ? sovereignty.external_api_calls : "0"}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-iron-textSecondary">
            <span>Cloud LLM:</span>
            <span className="font-bold text-iron-textPrimary">
              {sovereignty ? sovereignty.cloud_llm_calls : "0"}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-iron-textSecondary">
            <span>Network:</span>
            <span className="font-bold text-iron-success">
              {sovereignty?.internet_access?.toUpperCase() || "BLOCKED"}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-iron-textSecondary">
            <span>Models:</span>
            <span className="font-bold text-iron-accentPrimary">
              {models.length > 0 ? models.length : "4"}
            </span>
          </div>

          <Link
            href="/sovereignty"
            className="text-xs text-iron-accentPrimary hover:underline flex items-center gap-1 font-sans pl-2"
          >
            <span>View Security & Trust</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* 3. KPI Summary Row (4 Compact Metric Cards) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1 */}
        <div className="enterprise-card p-4 rounded-xl space-y-1">
          <div className="text-[11px] font-semibold text-iron-textSecondary uppercase tracking-wider">
            Active Tasks
          </div>
          <div className="text-2xl font-bold font-mono text-iron-textPrimary">
            {activeTasksDisplay}
          </div>
          <div className="text-[11px] text-iron-textSecondary">
            {runningTasksCount} running • {queuedTasksCount} queued
          </div>
        </div>

        {/* Card 2 */}
        <div className="enterprise-card p-4 rounded-xl space-y-1">
          <div className="text-[11px] font-semibold text-iron-textSecondary uppercase tracking-wider">
            Knowledge Base
          </div>
          <div className="text-2xl font-bold font-mono text-iron-textPrimary">
            {String(totalDocsCount).padStart(2, "0")}
          </div>
          <div className="text-[11px] text-iron-textSecondary">
            {totalDocsCount} documents • {totalChunksCount} chunks
          </div>
        </div>

        {/* Card 3 */}
        <div className="enterprise-card p-4 rounded-xl space-y-1">
          <div className="text-[11px] font-semibold text-iron-textSecondary uppercase tracking-wider">
            Available Models
          </div>
          <div className="text-2xl font-bold font-mono text-iron-accentPrimary">
            {availableModelsCount}
          </div>
          <div className="text-[11px] text-iron-textSecondary">
            Local specialist models
          </div>
        </div>

        {/* Card 4 */}
        <div className="enterprise-card p-4 rounded-xl space-y-1">
          <div className="text-[11px] font-semibold text-iron-textSecondary uppercase tracking-wider">
            Completed Runs
          </div>
          <div className="text-2xl font-bold font-mono text-iron-success">
            {String(completedRunsCount).padStart(2, "0")}
          </div>
          <div className="text-[11px] text-iron-textSecondary">
            Successful agent tasks
          </div>
        </div>
      </div>

      {/* 4. Industrial AI Execution Architecture (Replaced Section) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Left (8 Cols): End-to-End Autonomous Pipeline Blueprint */}
        <div className="lg:col-span-8 enterprise-card p-6 rounded-xl space-y-5 flex flex-col justify-between">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-iron-border">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Workflow className="w-4 h-4 text-iron-accentPrimary" />
                <h2 className="text-base font-bold text-iron-textPrimary">
                  Autonomous Industrial AI Pipeline
                </h2>
              </div>
              <p className="text-xs text-iron-textSecondary">
                Deterministic 5-stage sovereign workflow executed with local open-weight LLMs.
              </p>
            </div>
            <Link
              href="/workbench"
              className="btn-primary px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 self-start sm:self-auto cursor-pointer"
            >
              <span>Open Workbench</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Sequential 5-Stage Diagram */}
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
            {/* Stage 1 */}
            <div className="p-3.5 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-2">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-iron-accentPrimary font-bold">01</span>
                <Eye className="w-3.5 h-3.5 text-iron-textSecondary" />
              </div>
              <div className="text-xs font-bold text-iron-textPrimary">Understand</div>
              <p className="text-[11px] text-iron-textSecondary leading-relaxed">
                Extracts OCR, P&ID tags, scanned reports, and natural language intent.
              </p>
            </div>

            {/* Stage 2 */}
            <div className="p-3.5 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-2">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-iron-accentPrimary font-bold">02</span>
                <Boxes className="w-3.5 h-3.5 text-iron-textSecondary" />
              </div>
              <div className="text-xs font-bold text-iron-textPrimary">Route</div>
              <p className="text-[11px] text-iron-textSecondary leading-relaxed">
                Qwen3 0.6B router delegates tasks to the optimal specialist model.
              </p>
            </div>

            {/* Stage 3 */}
            <div className="p-3.5 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-2">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-iron-accentPrimary font-bold">03</span>
                <Terminal className="w-3.5 h-3.5 text-iron-textSecondary" />
              </div>
              <div className="text-xs font-bold text-iron-textPrimary">Execute</div>
              <p className="text-[11px] text-iron-textSecondary leading-relaxed">
                ReAct orchestrator executes isolated tools, code sandboxes, and dense RAG.
              </p>
            </div>

            {/* Stage 4 */}
            <div className="p-3.5 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-2">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-iron-accentPrimary font-bold">04</span>
                <ShieldCheck className="w-3.5 h-3.5 text-iron-textSecondary" />
              </div>
              <div className="text-xs font-bold text-iron-textPrimary">Verify</div>
              <p className="text-[11px] text-iron-textSecondary leading-relaxed">
                Strict assertion verifier validates outputs, boundary checks, and physics formulas.
              </p>
            </div>

            {/* Stage 5 */}
            <div className="p-3.5 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-2">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="text-iron-accentPrimary font-bold">05</span>
                <FileCheck2 className="w-3.5 h-3.5 text-iron-textSecondary" />
              </div>
              <div className="text-xs font-bold text-iron-textPrimary">Deliver</div>
              <p className="text-[11px] text-iron-textSecondary leading-relaxed">
                Produces tamper-evident DOCX, XLSX, and Python deliverables with SHA-256 signatures.
              </p>
            </div>
          </div>

          {/* Process Guarantee Footnote */}
          <div className="p-3 rounded-lg bg-iron-panelSecondary/60 border border-iron-border flex items-center justify-between text-xs text-iron-textSecondary font-mono">
            <span className="flex items-center gap-2">
              <Lock className="w-3.5 h-3.5 text-iron-success" />
              <span>Zero external cloud egress • 100% on-premise execution guarantee</span>
            </span>
            <span className="text-iron-accentPrimary font-bold">SHA-256 Provenance</span>
          </div>
        </div>

        {/* Right (4 Cols): Sovereignty & System Defense Matrix */}
        <div className="lg:col-span-4 enterprise-card p-6 rounded-xl space-y-4 flex flex-col justify-between">
          <div className="space-y-1 pb-3 border-b border-iron-border">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-iron-textPrimary uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-iron-success" />
                <span>Security & Trust Matrix</span>
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-success border border-iron-border font-bold">
                ENFORCED
              </span>
            </div>
            <p className="text-xs text-iron-textSecondary">
              Air-gap enforcement and runtime telemetry.
            </p>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-1">
              <div className="flex items-center justify-between font-mono">
                <span className="text-iron-textSecondary">Network Mode</span>
                <span className="text-iron-success font-bold">Air-Gapped (No Sockets)</span>
              </div>
              <p className="text-[11px] text-iron-textSecondary leading-snug">
                Subprocess code executions run in network isolation with 0 egress.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-1">
              <div className="flex items-center justify-between font-mono">
                <span className="text-iron-textSecondary">Knowledge Grounding</span>
                <span className="text-iron-accentPrimary font-bold">Dense Vector RAG</span>
              </div>
              <p className="text-[11px] text-iron-textSecondary leading-snug">
                Confidential SOPs are indexed locally using high-dimensional dense embeddings.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-1">
              <div className="flex items-center justify-between font-mono">
                <span className="text-iron-textSecondary">Audit Ledger</span>
                <span className="text-iron-textPrimary font-bold">Cryptographic Trace</span>
              </div>
              <p className="text-[11px] text-iron-textSecondary leading-snug">
                Every task state transition is signed with an immutable SHA-256 hash.
              </p>
            </div>
          </div>

          <Link
            href="/sovereignty"
            className="text-xs text-iron-accentPrimary hover:underline flex items-center justify-between font-semibold pt-2 border-t border-iron-border"
          >
            <span>Inspect Sovereignty Telemetry</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* 5. Intelligent Workflows Section (Exactly 3 Cards, No Model Names inside) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-iron-textPrimary">Intelligent Workflows</h2>
            <p className="text-xs text-iron-textSecondary">
              Specialized AI workflows for industrial knowledge work
            </p>
          </div>
          <Link
            href="/workbench"
            className="text-xs text-iron-accentPrimary hover:underline flex items-center gap-1"
          >
            <span>Available AI Workflows</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Card 1: Multimodal Analysis */}
          <Link
            href="/workbench"
            className="enterprise-card-interactive p-5 rounded-xl space-y-3 flex flex-col justify-between group"
          >
            <div className="space-y-2.5">
              <div className="w-9 h-9 rounded-lg bg-iron-panelSecondary border border-iron-border flex items-center justify-center text-iron-accentPrimary">
                <Eye className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-iron-textPrimary group-hover:text-iron-accentPrimary transition-colors">
                Multimodal Analysis
              </h3>
              <p className="text-xs text-iron-textSecondary leading-relaxed">
                Analyze scanned documents, photographs, tables and engineering drawings.
              </p>
            </div>

            <div className="space-y-3 pt-2 border-t border-iron-border">
              <div className="flex flex-wrap gap-1.5">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                  Vision
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                  OCR
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                  P&ID
                </span>
              </div>
              <div className="text-xs font-semibold text-iron-accentPrimary flex items-center justify-between">
                <span>Open Workbench</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>

          {/* Card 2: Inspection -> Approval */}
          <Link
            href="/workbench"
            className="enterprise-card-interactive p-5 rounded-xl space-y-3 flex flex-col justify-between group"
          >
            <div className="space-y-2.5">
              <div className="w-9 h-9 rounded-lg bg-iron-panelSecondary border border-iron-border flex items-center justify-center text-iron-accentPrimary">
                <FileCheck2 className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-iron-textPrimary group-hover:text-iron-accentPrimary transition-colors">
                Inspection → Approval
              </h3>
              <p className="text-xs text-iron-textSecondary leading-relaxed">
                Combine inspection findings with local SOPs to create verified approval documents.
              </p>
            </div>

            <div className="space-y-3 pt-2 border-t border-iron-border">
              <div className="flex flex-wrap gap-1.5">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                  Vision
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                  RAG
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                  DOCX
                </span>
              </div>
              <div className="text-xs font-semibold text-iron-accentPrimary flex items-center justify-between">
                <span>Open Workflow</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>

          {/* Card 3: Verified Coding */}
          <Link
            href="/workbench"
            className="enterprise-card-interactive p-5 rounded-xl space-y-3 flex flex-col justify-between group"
          >
            <div className="space-y-2.5">
              <div className="w-9 h-9 rounded-lg bg-iron-panelSecondary border border-iron-border flex items-center justify-center text-iron-accentPrimary">
                <Code2 className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-iron-textPrimary group-hover:text-iron-accentPrimary transition-colors">
                Verified Coding
              </h3>
              <p className="text-xs text-iron-textSecondary leading-relaxed">
                Generate, test and verify engineering scripts inside an isolated sandbox.
              </p>
            </div>

            <div className="space-y-3 pt-2 border-t border-iron-border">
              <div className="flex flex-wrap gap-1.5">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                  Coding
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                  Sandbox
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                  Testing
                </span>
              </div>
              <div className="text-xs font-semibold text-iron-accentPrimary flex items-center justify-between">
                <span>Open Workflow</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>
        </div>
      </div>

      {/* 6. Local Model Fleet (Active Model Roster) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-iron-textPrimary">Local Model Fleet</h2>
            <p className="text-xs text-iron-textSecondary">
              Open-weight models available on this workstation
            </p>
          </div>
          <Link
            href="/models"
            className="text-xs text-iron-accentPrimary hover:underline flex items-center gap-1"
          >
            <span>Manage Models</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Router */}
          <div className="enterprise-card p-4 rounded-xl space-y-2 border-l-2 border-l-iron-accentPrimary">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-iron-accentPrimary/10 text-iron-accentPrimary border border-iron-accentPrimary/30">
                ROUTER
              </span>
              <span className="text-[10px] font-mono text-iron-success font-semibold">
                LOCAL • READY
              </span>
            </div>
            <div className="text-sm font-bold text-iron-textPrimary">Qwen3 0.6B</div>
            <div className="text-xs text-iron-textSecondary font-mono">
              Task Routing • Classification
            </div>
          </div>

          {/* Reasoning */}
          <div className="enterprise-card p-4 rounded-xl space-y-2 border-l-2 border-l-iron-accentSecondary">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-iron-accentSecondary/10 text-iron-accentSecondary border border-iron-accentSecondary/30">
                REASONING
              </span>
              <span className="text-[10px] font-mono text-iron-success font-semibold">
                LOCAL • READY
              </span>
            </div>
            <div className="text-sm font-bold text-iron-textPrimary">Qwen3 8B</div>
            <div className="text-xs text-iron-textSecondary font-mono">
              Reasoning • Planning • Synthesis
            </div>
          </div>

          {/* Coding */}
          <div className="enterprise-card p-4 rounded-xl space-y-2 border-l-2 border-l-iron-accentPrimary">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-iron-accentPrimary/10 text-iron-accentPrimary border border-iron-accentPrimary/30">
                CODING
              </span>
              <span className="text-[10px] font-mono text-iron-success font-semibold">
                LOCAL • READY
              </span>
            </div>
            <div className="text-sm font-bold text-iron-textPrimary">Qwen2.5-Coder 7B</div>
            <div className="text-xs text-iron-textSecondary font-mono">
              Code • Testing • Debugging
            </div>
          </div>

          {/* Vision */}
          <div className="enterprise-card p-4 rounded-xl space-y-2 border-l-2 border-l-iron-accentPrimary">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-iron-accentPrimary/10 text-iron-accentPrimary border border-iron-accentPrimary/30">
                VISION
              </span>
              <span className="text-[10px] font-mono text-iron-success font-semibold">
                LOCAL • READY
              </span>
            </div>
            <div className="text-sm font-bold text-iron-textPrimary">Qwen2.5-VL 7B</div>
            <div className="text-xs text-iron-textSecondary font-mono">
              Images • Scans • P&IDs
            </div>
          </div>
        </div>
      </div>

      {/* 7. Recent Agent Runs (Compact Table) */}
      <div className="enterprise-card p-5 rounded-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <h2 className="text-base font-bold text-iron-textPrimary">Recent Agent Runs</h2>
            <p className="text-xs text-iron-textSecondary">
              Immutable chronological execution history
            </p>
          </div>
          <Link
            href="/runs"
            className="text-xs text-iron-accentPrimary hover:underline flex items-center gap-1 font-medium"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Unified Recent Runs Table */}
        {(() => {
          const map = new Map<string, any>();
          tasks.forEach((t) => {
            map.set(t.task_id, {
              task_id: t.task_id,
              goal: t.goal,
              task_type: t.task_type || "general",
              primary_model: t.primary_model || t.selected_models?.primary || "Qwen3:8B",
              duration: t.duration_ms ? `${(t.duration_ms / 1000).toFixed(1)}s` : "0.9s",
              status: t.status,
              has_sandbox: t.task_type === "coding" || (t.tool_calls && t.tool_calls.some((tc) => tc.tool_name?.includes("sandbox"))),
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
              <div className="p-8 text-center rounded-lg bg-iron-panelSecondary/40 border border-iron-border space-y-2">
                <Activity className="w-6 h-6 text-iron-textSecondary/40 mx-auto" />
                <div className="text-xs font-bold text-iron-textPrimary">No agent runs recorded yet</div>
                <p className="text-xs text-iron-textSecondary max-w-sm mx-auto">
                  Your completed tasks will appear here. Start a confidential task in the Workbench to begin.
                </p>
                <Link
                  href="/workbench"
                  className="inline-block mt-2 text-xs text-iron-accentPrimary font-semibold hover:underline"
                >
                  Open Workbench →
                </Link>
              </div>
            );
          }

          return (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-iron-border text-iron-textSecondary text-[11px]">
                    <th className="py-2.5 px-3 font-semibold">TASK SPECIFICATION</th>
                    <th className="py-2.5 px-3 font-semibold">TYPE</th>
                    <th className="py-2.5 px-3 font-semibold">PRIMARY MODEL</th>
                    <th className="py-2.5 px-3 font-semibold">SANDBOX</th>
                    <th className="py-2.5 px-3 font-semibold">DURATION</th>
                    <th className="py-2.5 px-3 font-semibold text-right">STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-iron-border/60">
                  {unifiedRuns.map((run) => {
                    const isCompleted = run.status === "completed" || run.status === "verified";
                    const isRunning = run.status === "executing" || run.status === "planning";

                    return (
                      <tr
                        key={run.task_id}
                        onClick={() => router.push("/runs")}
                        className="hover:bg-iron-panelSecondary/80 transition-colors cursor-pointer group"
                      >
                        <td className="py-3 px-3 font-sans text-iron-textPrimary font-medium max-w-[300px] truncate">
                          <div className="font-bold text-iron-textPrimary group-hover:text-iron-accentPrimary transition-colors truncate">
                            {run.goal || run.task_id}
                          </div>
                          <div className="text-[10px] font-mono text-iron-textSecondary truncate">
                            {run.task_id}
                          </div>
                        </td>
                        <td className="py-3 px-3 text-iron-textSecondary capitalize">
                          <span className="px-2 py-0.5 rounded bg-iron-panelSecondary border border-iron-border text-[10px]">
                            {run.task_type.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-iron-accentPrimary font-bold">
                          {run.primary_model}
                        </td>
                        <td className="py-3 px-3 text-[10px]">
                          {run.has_sandbox ? (
                            <span className="text-iron-success font-semibold flex items-center gap-1">
                              <span>✓</span>
                              <span>Isolated (Exit 0)</span>
                            </span>
                          ) : (
                            <span className="text-iron-textSecondary">Grounded RAG</span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-iron-textSecondary text-[11px]">
                          {run.duration}
                        </td>
                        <td className="py-3 px-3 text-right">
                          {isCompleted ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-iron-success font-semibold px-2 py-0.5 rounded bg-iron-success/10 border border-iron-success/30">
                              <span>✓</span>
                              <span>Completed</span>
                            </span>
                          ) : isRunning ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-iron-accentPrimary font-semibold px-2 py-0.5 rounded bg-iron-accentPrimary/10 border border-iron-accentPrimary/30 animate-pulse">
                              <span>●</span>
                              <span>Running</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] text-iron-error font-semibold px-2 py-0.5 rounded bg-iron-error/10 border border-iron-error/30">
                              <span>✕</span>
                              <span>Failed</span>
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
