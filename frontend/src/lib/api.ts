import type {
  AlertOut, ApplicationHistoryOut, ApplicationOut, ChatMessageOut, ComplianceCheckResponse,
  ComplianceResultOut, ComplianceRuleOut, DocumentOut, LoginResponse, OfficerOut, QueryOut,
  QueryResponseOut, ScanResultOut, SummaryOut, UserPublic,
} from "./types";

const BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api").replace(/\/$/, "");
const TOKEN_KEY = "approvedesk_token";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

interface RequestOptions { method?: string; body?: unknown; form?: FormData; }

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload: BodyInit | undefined;
  if (options.form) {
    payload = options.form;
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(options.body);
  }
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, { method: options.method ?? "GET", headers, body: payload });
  } catch {
    throw new ApiError("Cannot reach the API server. Is the backend running?", 0);
  }
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail;
    const message = typeof detail === "string" ? detail
      : detail ? JSON.stringify(detail)
      : `Request failed (${response.status})`;
    throw new ApiError(message, response.status);
  }
  return data as T;
}

export const api = {
  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login", { method: "POST", body: { email, password } }),
  me: () => request<UserPublic>("/auth/me"),

  listApplications: (status?: string) =>
    request<ApplicationOut[]>(`/applications${status ? `?status=${status}` : ""}`),
  getApplication: (id: number) => request<ApplicationOut>(`/applications/${id}`),
  createApplication: (body: { title: string; description?: string; submitted_data?: Record<string, unknown>; due_at?: string }) =>
    request<ApplicationOut>("/applications", { method: "POST", body }),
  updateApplicationData: (id: number, submitted_data: Record<string, unknown>) =>
    request<ApplicationOut>(`/applications/${id}/data`, { method: "PATCH", body: { submitted_data } }),
  transition: (id: number, to_stage: string, note?: string) =>
    request<ApplicationOut>(`/applications/${id}/transition`, { method: "POST", body: { to_stage, note } }),
  assignOfficer: (id: number, assigned_officer_id: number) =>
    request<ApplicationOut>(`/applications/${id}/assignment`, { method: "PATCH", body: { assigned_officer_id } }),
  getHistory: (id: number) => request<ApplicationHistoryOut>(`/applications/${id}/history`),
  listQueries: (id: number) => request<QueryOut[]>(`/applications/${id}/queries`),
  createQuery: (id: number, message: string, due_at?: string) =>
    request<QueryOut>(`/applications/${id}/queries`, { method: "POST", body: { message, due_at } }),
  listQueryResponses: (queryId: number) => request<QueryResponseOut[]>(`/queries/${queryId}/responses`),
  respondToQuery: (queryId: number, message: string) =>
    request<QueryResponseOut>(`/queries/${queryId}/responses`, { method: "POST", body: { message } }),
  listDocuments: (id: number) => request<DocumentOut[]>(`/applications/${id}/documents`),
  uploadDocument: (id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentOut>(`/applications/${id}/documents`, { method: "POST", form });
  },

  listComplianceRules: () => request<ComplianceRuleOut[]>("/compliance/rules"),
  createComplianceRule: (body: Record<string, unknown>) =>
    request<ComplianceRuleOut>("/compliance/rules", { method: "POST", body }),
  updateComplianceRule: (id: number, body: Record<string, unknown>) =>
    request<ComplianceRuleOut>(`/compliance/rules/${id}`, { method: "PATCH", body }),
  runComplianceCheck: (id: number) =>
    request<ComplianceCheckResponse>(`/applications/${id}/compliance/check`, { method: "POST" }),
  getComplianceResults: (id: number) =>
    request<ComplianceResultOut[]>(`/applications/${id}/compliance/results`),

  listAlerts: () => request<AlertOut[]>("/alerts"),
  acknowledgeAlert: (id: number) =>
    request<AlertOut>(`/alerts/${id}/acknowledge`, { method: "POST" }),
  scanAlerts: () => request<ScanResultOut>("/alerts/scan", { method: "POST" }),

  listOfficers: () => request<OfficerOut[]>("/users/officers"),

  sendChatMessage: (message: string, applicationId?: number, conversationId?: number) =>
    request<ChatMessageOut>("/chat/messages", {
      method: "POST",
      body: { message, application_id: applicationId ?? null, conversation_id: conversationId ?? null },
    }),
  getSummary: (id: number) => request<SummaryOut>(`/applications/${id}/summary`),
};
