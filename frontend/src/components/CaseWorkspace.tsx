"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type {
  AlertOut, ApplicationHistoryOut, ApplicationOut, ComplianceResultOut, DocumentOut,
  QueryOut, QueryResponseOut, StageHistoryOut,
} from "@/lib/types";
import { NEXT_STAGES, STAGE_LABELS, WORKFLOW_STAGES } from "@/lib/types";
import { ComplianceBadge, EmptyState, ErrorState, SeverityBadge, Spinner, StageBadge, fmtDate } from "./ui";
import { AiChat } from "./AiChat";

type Tab = "overview" | "documents" | "compliance" | "queries" | "audit";

const QUERY_STATUS_LABEL: Record<string, string> = { OPEN: "Open", RESPONDED: "Responded", CLOSED: "Closed" };

export function CaseWorkspace({ mode }: { mode: "officer" | "institution" }) {
  const params = useParams<{ id: string }>();
  const applicationId = Number(params.id);

  const [app, setApp] = useState<ApplicationOut | null>(null);
  const [history, setHistory] = useState<ApplicationHistoryOut | null>(null);
  const [queries, setQueries] = useState<QueryOut[]>([]);
  const [responses, setResponses] = useState<Record<number, QueryResponseOut[]>>({});
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [results, setResults] = useState<ComplianceResultOut[]>([]);
  const [alerts, setAlerts] = useState<AlertOut[]>([]);
  const [tab, setTab] = useState<Tab>("overview");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyAction, setBusyAction] = useState("");

  const load = useCallback(() => {
    Promise.all([
      api.getApplication(applicationId),
      api.getHistory(applicationId),
      api.listQueries(applicationId),
      api.listDocuments(applicationId),
      api.getComplianceResults(applicationId),
      api.listAlerts().catch(() => [] as AlertOut[]),
    ])
      .then(([appData, historyData, queryData, docData, resultData, alertData]) => {
        setApp(appData);
        setHistory(historyData);
        setQueries(queryData);
        setDocuments(docData);
        setResults(resultData);
        setAlerts(alertData.filter((a) => a.application_id === applicationId));
        setError("");
        return Promise.all(
          queryData.map((query) =>
            api.listQueryResponses(query.id)
              .catch(() => [] as QueryResponseOut[])
              .then((items) => [query.id, items] as const),
          ),
        );
      })
      .then((entries) => { setResponses(Object.fromEntries(entries)); })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load the case."));
  }, [applicationId]);

  useEffect(() => { load(); }, [load]);

  async function runAction(label: string, action: () => Promise<unknown>, successMessage: string) {
    setNotice("");
    setError("");
    setBusyAction(label);
    try {
      await action();
      setNotice(successMessage);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setBusyAction("");
    }
  }

  const latestPerRule = useMemo(() => {
    const map = new Map<string, ComplianceResultOut>();
    for (const result of results) if (!map.has(result.rule_code)) map.set(result.rule_code, result);
    return [...map.values()];
  }, [results]);

  if (error && !app) return <ErrorState message={error} onRetry={load} />;
  if (!app || !history) return <Spinner label="Loading case..." />;

  const openAlerts = alerts.filter((a) => a.status === "OPEN");
  const stageIndex = WORKFLOW_STAGES.indexOf(app.current_stage);

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{app.application_code}</p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight">{app.title}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <StageBadge stage={app.current_stage} />
              <span className="text-sm text-slate-600">Deadline: {fmtDate(app.due_at)}</span>
              {app.assigned_officer_id && <span className="text-sm text-slate-600">Officer ID: {app.assigned_officer_id}</span>}
            </div>
          </div>
          {mode === "officer" && (
            <div className="flex flex-wrap gap-2">
              {NEXT_STAGES[app.current_stage].map((stage) => (
                <button key={stage} disabled={busyAction !== ""}
                  onClick={() => runAction(stage, () => api.transition(app.id, stage),
                    `Stage updated to ${STAGE_LABELS[stage]}.`)}
                  className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-bold text-white hover:bg-orange-700 disabled:opacity-50">
                  {stage === "CORRECTION_REQUIRED" ? "Request correction" : `Advance to ${STAGE_LABELS[stage]}`}
                </button>
              ))}
              {NEXT_STAGES[app.current_stage].length === 0 && (
                <span className="rounded-lg bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-600">No further transitions</span>
              )}
            </div>
          )}
        </div>
        {app.description && <p className="mt-3 text-sm text-slate-600">{app.description}</p>}
        {notice && <p className="mt-3 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</p>}
        {error && <p role="alert" className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      </section>

      {openAlerts.length > 0 && (
        <section className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm font-bold text-amber-900">Active alerts on this case</p>
          <ul className="mt-2 space-y-2">
            {openAlerts.map((alert) => (
              <li key={alert.id} className="flex flex-wrap items-center gap-2 text-sm">
                <SeverityBadge severity={alert.severity} />
                <span className="font-semibold text-amber-900">{alert.alert_type.replaceAll("_", " ")}</span>
                <span className="text-amber-800">{alert.message}</span>
                {mode === "officer" && (
                  <button disabled={busyAction !== ""}
                    onClick={() => runAction("ack", () => api.acknowledgeAlert(alert.id), "Alert acknowledged.")}
                    className="rounded-lg border border-amber-300 bg-white px-3 py-1 text-xs font-bold text-amber-900 hover:bg-amber-100">
                    Acknowledge
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      <nav className="flex flex-wrap gap-2">
        {(["overview", "documents", "compliance", "queries", "audit"] as Tab[]).map((item) => (
          <button key={item} onClick={() => setTab(item)}
            className={`rounded-lg px-4 py-2 text-sm font-semibold capitalize ${
              tab === item ? "bg-slate-900 text-white" : "border border-slate-200 bg-white hover:bg-slate-100"
            }`}>
            {item}
          </button>
        ))}
      </nav>

      {tab === "overview" && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-bold">Stage timeline</h2>
          <ol className="mt-4 space-y-0">
            {history.stages.map((entry: StageHistoryOut) => {
              const reached = WORKFLOW_STAGES.indexOf(entry.to_stage as never) <= stageIndex;
              return (
                <li key={entry.id} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <span className={`flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold ${
                      reached ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-500"
                    }`}>✓</span>
                    <span className="h-6 w-px bg-slate-200" />
                  </div>
                  <div className="pb-4">
                    <p className="text-sm font-semibold">{STAGE_LABELS[entry.to_stage as never] ?? entry.to_stage}</p>
                    <p className="text-xs text-slate-500">{fmtDate(entry.created_at)}{entry.note ? ` · ${entry.note}` : ""}</p>
                  </div>
                </li>
              );
            })}
          </ol>
          <h3 className="mt-4 text-sm font-bold uppercase tracking-wide text-slate-500">Submitted data</h3>
          {app.submitted_data && Object.keys(app.submitted_data).length > 0 ? (
            <table className="mt-2 w-full text-sm">
              <tbody>
                {Object.entries(app.submitted_data).map(([key, value]) => (
                  <tr key={key} className="border-t border-slate-100">
                    <td className="py-2 pr-4 font-mono text-slate-600">{key}</td>
                    <td className="py-2 font-semibold">{String(value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="mt-2 text-sm text-slate-500">No structured data submitted.</p>
          )}
          {mode === "institution" && <DataCorrectionForm app={app} onSaved={() => runAction("data", async () => {}, "Declared data updated.")} />}
        </section>
      )}

      {tab === "documents" && <DocumentsPanel appId={app.id} documents={documents} canUpload onChanged={load} />}

      {tab === "compliance" && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold">Compliance results</h2>
              <p className="mt-1 text-xs text-slate-500">
                Sample rules are demo-only assumptions, not verified official requirements.
              </p>
            </div>
            {mode === "officer" && (
              <button disabled={busyAction !== ""}
                onClick={() => runAction("check", () => api.runComplianceCheck(app.id), "Compliance check completed.")}
                className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-bold text-white hover:bg-orange-700 disabled:opacity-50">
                Run compliance check
              </button>
            )}
          </div>
          {latestPerRule.length === 0 ? (
            <EmptyState title="No compliance results yet" hint={mode === "officer" ? "Run a compliance check to evaluate the saved data." : "Results appear after an officer runs a check."} />
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[42rem] text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                    <th className="py-2 pr-3">Rule</th>
                    <th className="py-2 pr-3">Expected</th>
                    <th className="py-2 pr-3">Actual</th>
                    <th className="py-2 pr-3">Status</th>
                    <th className="py-2 pr-3">Evaluated</th>
                    <th className="py-2">Finding</th>
                  </tr>
                </thead>
                <tbody>
                  {latestPerRule.map((result) => (
                    <tr key={result.id} className="border-b border-slate-100 align-top">
                      <td className="py-2 pr-3 font-mono text-xs">{result.rule_code} <span className="text-slate-400">v{result.rule_version}</span></td>
                      <td className="py-2 pr-3">{String(result.expected)}{result.unit ? ` ${result.unit}` : ""}</td>
                      <td className="py-2 pr-3">{String(result.actual)}</td>
                      <td className="py-2 pr-3"><ComplianceBadge status={result.status} /></td>
                      <td className="py-2 pr-3 text-xs text-slate-500">{fmtDate(result.evaluated_at)}</td>
                      <td className="py-2 text-xs text-slate-600">{result.explanation}{result.gap !== null && result.gap !== undefined ? ` Gap: ${result.gap}.` : ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {results.length > latestPerRule.length && (
            <p className="mt-3 text-xs text-slate-500">Earlier evaluation runs are preserved in the audit history ({results.length} total result records).</p>
          )}
        </section>
      )}

      {tab === "queries" && (
        <QueriesPanel
          mode={mode}
          appId={app.id}
          queries={queries}
          responses={responses}
          onChanged={(message) => runAction("query", async () => {}, message)}
        />
      )}

      {tab === "audit" && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-bold">Audit trail</h2>
          {history.audit_events.length === 0 ? (
            <EmptyState title="No audit events" />
          ) : (
            <ul className="mt-4 space-y-2">
              {[...history.audit_events].reverse().map((event) => (
                <li key={event.id} className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-sm">
                  <span className="font-mono text-xs font-bold text-slate-700">{event.action}</span>
                  <span className="ml-2 text-xs text-slate-500">{fmtDate(event.created_at)} · actor #{event.actor_id ?? "system"}</span>
                  {event.details && (
                    <span className="mt-1 block font-mono text-[11px] text-slate-500">{JSON.stringify(event.details)}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <AiChat applicationId={app.id} />
    </div>
  );
}

function DataCorrectionForm({ app, onSaved }: { app: ApplicationOut; onSaved: () => void }) {
  const [faculty, setFaculty] = useState(String(app.submitted_data?.faculty_count ?? ""));
  const [infra, setInfra] = useState(String(app.submitted_data?.infrastructure_capacity ?? ""));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const merged: Record<string, unknown> = { ...(app.submitted_data ?? {}) };
    if (faculty !== "") merged.faculty_count = Number(faculty);
    if (infra !== "") merged.infrastructure_capacity = Number(infra);
    try {
      await api.updateApplicationData(app.id, merged);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save} className="mt-4 rounded-lg border border-slate-200 p-4">
      <p className="text-sm font-bold">Update declared data (correction)</p>
      <p className="mt-1 text-xs text-slate-500">Corrections are audit-logged and can be re-checked by the reviewing officer.</p>
      <div className="mt-3 flex flex-wrap gap-3">
        <label className="text-xs font-semibold">faculty_count
          <input value={faculty} onChange={(e) => setFaculty(e.target.value)} type="number" min={0}
            className="mt-1 block rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </label>
        <label className="text-xs font-semibold">infrastructure_capacity
          <input value={infra} onChange={(e) => setInfra(e.target.value)} type="number" min={0}
            className="mt-1 block rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </label>
      </div>
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
      <button type="submit" disabled={busy}
        className="mt-3 rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white hover:bg-slate-700 disabled:opacity-50">
        {busy ? "Saving..." : "Save corrected data"}
      </button>
    </form>
  );
}

function DocumentsPanel({ appId, documents, canUpload, onChanged }: {
  appId: number; documents: DocumentOut[]; canUpload: boolean; onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function upload(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      await api.uploadDocument(appId, file);
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold">Documents</h2>
      {documents.length === 0 ? (
        <EmptyState title="No documents uploaded" hint="Upload a PDF or text evidence file (max 10 MiB)." />
      ) : (
        <ul className="mt-4 space-y-2">
          {documents.map((doc) => (
            <li key={doc.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-sm">
              <span className="font-semibold">{doc.filename}</span>
              <span className="text-xs text-slate-500">
                {doc.verified ? "Verified" : "Not yet verified"} · {fmtDate(doc.created_at)}
              </span>
            </li>
          ))}
        </ul>
      )}
      {canUpload && (
        <div className="mt-4">
          <label className="inline-flex cursor-pointer rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-100">
            {busy ? "Uploading..." : "Upload document"}
            <input type="file" className="hidden" disabled={busy} onChange={(e) => { void upload(e.target.files?.[0]); e.target.value = ""; }} />
          </label>
          {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
        </div>
      )}
    </section>
  );
}

function QueriesPanel({ mode, appId, queries, responses, onChanged }: {
  mode: "officer" | "institution"; appId: number;
  queries: QueryOut[]; responses: Record<number, QueryResponseOut[]>;
  onChanged: (message: string) => void;
}) {
  const [message, setMessage] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [responsesDraft, setResponsesDraft] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function raiseQuery(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.createQuery(appId, message, dueAt ? new Date(dueAt).toISOString() : undefined);
      setMessage("");
      setDueAt("");
      onChanged("Query raised. The institution has been asked to respond.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not raise the query.");
    } finally {
      setBusy(false);
    }
  }

  async function respond(queryId: number) {
    const text = (responsesDraft[queryId] ?? "").trim();
    if (!text) return;
    setBusy(true);
    setError("");
    try {
      await api.respondToQuery(queryId, text);
      setResponsesDraft((prev) => ({ ...prev, [queryId]: "" }));
      onChanged("Response submitted. The case now awaits officer re-review; this does not mean approval.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit the response.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold">Queries</h2>
      {queries.length === 0 && <EmptyState title="No queries on this case" />}
      <ul className="mt-4 space-y-4">
        {queries.map((query) => (
          <li key={query.id} className="rounded-lg border border-slate-200 p-4">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className={`rounded-full px-2 py-0.5 font-bold ${
                query.status === "OPEN" ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-600"
              }`}>{QUERY_STATUS_LABEL[query.status] ?? query.status}</span>
              <span className="text-slate-500">Query #{query.id} · {fmtDate(query.created_at)}
                {query.due_at ? ` · response due ${fmtDate(query.due_at)}` : ""}</span>
            </div>
            <p className="mt-2 text-sm">{query.message}</p>
            {(responses[query.id] ?? []).map((response) => (
              <p key={response.id} className="mt-2 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
                <span className="text-xs font-bold text-slate-500">Response · {fmtDate(response.created_at)}</span><br />
                {response.message}
              </p>
            ))}
            {mode === "institution" && query.status !== "CLOSED" && (
              <div className="mt-3 flex gap-2">
                <input value={responsesDraft[query.id] ?? ""} onChange={(e) => setResponsesDraft((p) => ({ ...p, [query.id]: e.target.value }))}
                  placeholder="Write your response..." className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                <button onClick={() => respond(query.id)} disabled={busy}
                  className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-bold text-white hover:bg-orange-700 disabled:opacity-50">
                  Respond
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>
      {mode === "officer" && (
        <form onSubmit={raiseQuery} className="mt-5 rounded-lg border border-slate-200 p-4">
          <p className="text-sm font-bold">Raise a query</p>
          <textarea value={message} onChange={(e) => setMessage(e.target.value)} required rows={3}
            placeholder="e.g. Please submit corrected faculty evidence..." className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <label className="text-xs font-semibold text-slate-600">Response due
              <input type="datetime-local" value={dueAt} onChange={(e) => setDueAt(e.target.value)}
                className="mt-1 block rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </label>
            <button type="submit" disabled={busy}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white hover:bg-slate-700 disabled:opacity-50">
              {busy ? "Sending..." : "Raise query"}
            </button>
          </div>
        </form>
      )}
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </section>
  );
}
