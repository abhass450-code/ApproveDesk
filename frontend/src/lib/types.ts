export type Role = "INSTITUTION" | "OFFICER" | "ADMIN";

export const WORKFLOW_STAGES = [
  "SUBMITTED", "INITIAL_SCRUTINY", "DOCUMENT_VERIFICATION", "COMPLIANCE_CHECK",
  "OFFICER_REVIEW", "INSPECTION", "FINAL_REVIEW", "CORRECTION_REQUIRED",
  "APPROVED", "REJECTED",
] as const;
export type ApplicationStatus = (typeof WORKFLOW_STAGES)[number];

export type QueryStatus = "OPEN" | "RESPONDED" | "CLOSED";
export type ComplianceStatus = "PASS" | "FAIL" | "WARNING" | "NEEDS_REVIEW";
export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type AlertStatus = "OPEN" | "ACKNOWLEDGED" | "RESOLVED";
export type AlertType =
  | "DEADLINE_SOON" | "OVERDUE_STAGE" | "COMPLIANCE_FAILURE"
  | "DOCUMENT_EXPIRING" | "QUERY_RESPONSE_OVERDUE";

export interface UserPublic {
  id: number; email: string; full_name: string; role: Role; institution_id: number | null;
}
export interface LoginResponse { access_token: string; token_type: string; user: UserPublic; }

export interface ApplicationOut {
  id: number; application_code: string; institution_id: number; created_by_id: number;
  assigned_officer_id: number | null; title: string; description: string | null;
  current_stage: ApplicationStatus; correction_return_stage: ApplicationStatus | null;
  submitted_data: Record<string, unknown> | null; due_at: string | null;
  created_at: string; updated_at: string;
}
export interface StageHistoryOut {
  id: number; application_id: number; from_stage: string | null; to_stage: string;
  changed_by_id: number | null; note: string | null; created_at: string;
}
export interface AuditLogOut {
  id: number; actor_id: number | null; action: string; entity_type: string;
  entity_id: number | null; details: Record<string, unknown> | null; created_at: string;
}
export interface ApplicationHistoryOut {
  application_id: number; stages: StageHistoryOut[]; audit_events: AuditLogOut[];
}
export interface QueryOut {
  id: number; application_id: number; raised_by_id: number | null; message: string;
  due_at: string | null; status: QueryStatus; created_at: string;
}
export interface QueryResponseOut {
  id: number; query_id: number; responder_id: number | null; message: string; created_at: string;
}
export interface DocumentOut {
  id: number; application_id: number; filename: string; content_type: string | null;
  verified: boolean; created_at: string;
}

export interface ComplianceRuleOut {
  id: number; code: string; name: string; category: string; field_key: string; operator: string;
  threshold_value: unknown; unit: string | null; severity: Severity; active: boolean; version: number;
  demo_only: boolean; source_title: string | null; source_url: string | null;
  source_clause: string | null; description: string | null; created_at: string; updated_at: string;
}
export interface ComplianceResultOut {
  id: number; application_id: number; rule_id: number | null; rule_code: string; rule_version: number;
  field_key: string; expected: unknown; actual: unknown; unit: string | null; status: ComplianceStatus;
  gap: number | null; explanation: string | null; evidence_document_ids: number[] | null;
  evaluated_at: string;
}
export interface ComplianceCheckResponse {
  application_id: number; evaluated_at: string;
  summary: { total: number; passed: number; failed: number; warnings: number; needs_review: number };
  results: ComplianceResultOut[];
}

export interface AlertOut {
  id: number; application_id: number; recipient_id: number | null; alert_type: AlertType;
  severity: Severity; message: string; due_at: string | null; status: AlertStatus;
  dedupe_key: string; created_at: string; acknowledged_at: string | null;
}
export interface ScanResultOut { created: number; skipped: number; }

export interface ChatSource { type: string; id: string; label: string; }
export interface SuggestedAction { label: string; route: string; }
export interface ChatMessageOut {
  conversation_id: number; answer: string; sources: ChatSource[];
  suggested_actions: SuggestedAction[]; used_ai: boolean; needs_human_review: boolean;
}
export interface SummaryOut {
  application_id: number; summary: string; next_action: string; generated_by: "deterministic" | "ai";
}
export interface OfficerOut { id: number; full_name: string; email: string; }

export const NEXT_STAGES: Record<ApplicationStatus, ApplicationStatus[]> = {
  SUBMITTED: ["INITIAL_SCRUTINY", "CORRECTION_REQUIRED"],
  INITIAL_SCRUTINY: ["DOCUMENT_VERIFICATION", "CORRECTION_REQUIRED"],
  DOCUMENT_VERIFICATION: ["COMPLIANCE_CHECK", "CORRECTION_REQUIRED"],
  COMPLIANCE_CHECK: ["OFFICER_REVIEW", "CORRECTION_REQUIRED"],
  OFFICER_REVIEW: ["INSPECTION", "CORRECTION_REQUIRED"],
  INSPECTION: ["FINAL_REVIEW", "CORRECTION_REQUIRED"],
  FINAL_REVIEW: ["APPROVED", "REJECTED", "CORRECTION_REQUIRED"],
  CORRECTION_REQUIRED: [],
  APPROVED: [],
  REJECTED: [],
};

export const STAGE_LABELS: Record<ApplicationStatus, string> = {
  SUBMITTED: "Submitted", INITIAL_SCRUTINY: "Initial Scrutiny",
  DOCUMENT_VERIFICATION: "Document Verification", COMPLIANCE_CHECK: "Compliance Check",
  OFFICER_REVIEW: "Officer Review", INSPECTION: "Inspection", FINAL_REVIEW: "Final Review",
  CORRECTION_REQUIRED: "Correction Required", APPROVED: "Approved", REJECTED: "Rejected",
};

export const TERMINAL_STAGES: ApplicationStatus[] = ["APPROVED", "REJECTED"];

export function roleHome(role: Role): string {
  if (role === "OFFICER") return "/officer/dashboard";
  if (role === "ADMIN") return "/admin/dashboard";
  return "/institution/dashboard";
}
