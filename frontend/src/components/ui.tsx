"use client";

import type { ApplicationStatus, ComplianceStatus, Severity } from "@/lib/types";
import { STAGE_LABELS, TERMINAL_STAGES } from "@/lib/types";

export function KpiCard({ label, value, tone = "slate" }: { label: string; value: number | string; tone?: "slate" | "green" | "red" | "amber" }) {
  const tones: Record<string, string> = {
    slate: "text-slate-900", green: "text-emerald-600", red: "text-red-600", amber: "text-amber-600",
  };
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-3 text-3xl font-bold ${tones[tone]}`}>{value}</p>
    </div>
  );
}

const STAGE_STYLES: Record<ApplicationStatus, string> = {
  SUBMITTED: "bg-slate-100 text-slate-700 border-slate-300",
  INITIAL_SCRUTINY: "bg-blue-50 text-blue-700 border-blue-300",
  DOCUMENT_VERIFICATION: "bg-blue-50 text-blue-700 border-blue-300",
  COMPLIANCE_CHECK: "bg-amber-50 text-amber-800 border-amber-300",
  OFFICER_REVIEW: "bg-amber-50 text-amber-800 border-amber-300",
  INSPECTION: "bg-amber-50 text-amber-800 border-amber-300",
  FINAL_REVIEW: "bg-violet-50 text-violet-700 border-violet-300",
  CORRECTION_REQUIRED: "bg-red-50 text-red-700 border-red-300",
  APPROVED: "bg-emerald-50 text-emerald-700 border-emerald-300",
  REJECTED: "bg-red-50 text-red-700 border-red-300",
};

export function StageBadge({ stage }: { stage: ApplicationStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-bold ${STAGE_STYLES[stage] ?? STAGE_STYLES.SUBMITTED}`}>
      {STAGE_LABELS[stage] ?? stage}
    </span>
  );
}

export function ComplianceBadge({ status }: { status: ComplianceStatus }) {
  const styles: Record<ComplianceStatus, string> = {
    PASS: "bg-emerald-50 text-emerald-700 border-emerald-300",
    FAIL: "bg-red-50 text-red-700 border-red-300",
    WARNING: "bg-amber-50 text-amber-800 border-amber-300",
    NEEDS_REVIEW: "bg-slate-100 text-slate-700 border-slate-300",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-bold ${styles[status]}`}>
      {status.replace("_", " ")}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  const styles: Record<Severity, string> = {
    LOW: "bg-slate-100 text-slate-700 border-slate-300",
    MEDIUM: "bg-amber-50 text-amber-800 border-amber-300",
    HIGH: "bg-red-50 text-red-700 border-red-300",
    CRITICAL: "bg-red-100 text-red-800 border-red-400",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-bold ${styles[severity]}`}>
      {severity}
    </span>
  );
}

export function Spinner({ label = "Loading..." }: { label?: string }) {
  return <p role="status" className="py-10 text-center text-slate-500">{label}</p>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
      <p className="font-semibold">Something went wrong</p>
      <p className="mt-1 text-sm">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 rounded-lg bg-red-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-red-700">
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="py-10 text-center">
      <p className="font-semibold text-slate-700">{title}</p>
      {hint && <p className="mt-1 text-sm text-slate-500">{hint}</p>}
    </div>
  );
}

export function fmtDate(value: string | null | undefined): string {
  if (!value) return "Not set";
  return new Date(value).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}

export function isOverdue(dueAt: string | null | undefined, stage: ApplicationStatus): boolean {
  if (!dueAt || TERMINAL_STAGES.includes(stage)) return false;
  return new Date(dueAt).getTime() < Date.now();
}

export function isDueSoon(dueAt: string | null | undefined, stage: ApplicationStatus): boolean {
  if (!dueAt || TERMINAL_STAGES.includes(stage)) return false;
  const diff = new Date(dueAt).getTime() - Date.now();
  return diff > 0 && diff <= 48 * 60 * 60 * 1000;
}
