"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { EmptyState, ErrorState, SeverityBadge, Spinner, fmtDate } from "@/components/ui";
import { api } from "@/lib/api";
import type { AlertOut, ScanResultOut } from "@/lib/types";

export default function AdminAlertsPage() {
  const [alerts, setAlerts] = useState<AlertOut[] | null>(null);
  const [error, setError] = useState("");
  const [scanResult, setScanResult] = useState<ScanResultOut | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.listAlerts()
      .then((data) => { setAlerts(data); setError(""); })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed."));
  }, []);
  useEffect(() => { load(); }, [load]);

  async function runScan() {
    setBusy(true);
    setError("");
    try {
      const result = await api.scanAlerts();
      setScanResult(result);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scan failed.");
    } finally {
      setBusy(false);
    }
  }

  async function acknowledge(id: number) {
    setError("");
    try {
      await api.acknowledgeAlert(id);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Acknowledge failed.");
    }
  }

  const openCount = (alerts ?? []).filter((a) => a.status === "OPEN").length;

  return (
    <AppShell roles={["ADMIN"]}>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Alert centre</h1>
            <p className="mt-1 text-sm text-slate-600">
              {alerts === null ? "Loading..." : `${openCount} open alert(s). Repeat scans do not create duplicates.`}
            </p>
          </div>
          <button onClick={runScan} disabled={busy}
            className="rounded-lg bg-orange-600 px-5 py-2.5 text-sm font-bold text-white hover:bg-orange-700 disabled:opacity-50">
            {busy ? "Scanning..." : "Run alert scan"}
          </button>
        </div>

        {scanResult && (
          <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">
            Scan complete: {scanResult.created} alert(s) created, {scanResult.skipped} skipped (already open).
          </p>
        )}
        {error && <div className="p-1"><ErrorState message={error} onRetry={load} /></div>}

        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          {alerts === null ? (
            <Spinner label="Loading alerts..." />
          ) : alerts.length === 0 ? (
            <EmptyState title="No alerts" hint="Run a scan after seeding or creating cases with deadlines." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[46rem] text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                    <th className="px-5 py-3">Severity</th>
                    <th className="px-5 py-3">Type</th>
                    <th className="px-5 py-3">Message</th>
                    <th className="px-5 py-3">Case</th>
                    <th className="px-5 py-3">Deadline</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((alert) => (
                    <tr key={alert.id} className="border-b border-slate-100 align-top">
                      <td className="px-5 py-3"><SeverityBadge severity={alert.severity} /></td>
                      <td className="px-5 py-3 text-xs font-semibold">{alert.alert_type.replaceAll("_", " ")}</td>
                      <td className="px-5 py-3 text-xs text-slate-600">{alert.message}</td>
                      <td className="px-5 py-3 text-xs">#{alert.application_id}</td>
                      <td className="px-5 py-3 text-xs text-slate-500">{fmtDate(alert.due_at)}</td>
                      <td className="px-5 py-3">
                        <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
                          alert.status === "OPEN" ? "bg-red-50 text-red-700" : "bg-slate-100 text-slate-600"
                        }`}>{alert.status}</span>
                      </td>
                      <td className="px-5 py-3">
                        {alert.status === "OPEN" && (
                          <button onClick={() => acknowledge(alert.id)}
                            className="rounded-lg border border-slate-300 px-3 py-1 text-xs font-bold hover:bg-slate-100">
                            Acknowledge
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
