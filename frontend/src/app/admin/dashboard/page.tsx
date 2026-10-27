"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { EmptyState, ErrorState, KpiCard, Spinner, StageBadge, fmtDate, isOverdue } from "@/components/ui";
import { api } from "@/lib/api";
import type { ApplicationOut, OfficerOut } from "@/lib/types";
import { TERMINAL_STAGES } from "@/lib/types";

export default function AdminDashboard() {
  const [apps, setApps] = useState<ApplicationOut[] | null>(null);
  const [officers, setOfficers] = useState<OfficerOut[]>([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState<number | null>(null);

  const load = useCallback(() => {
    Promise.all([api.listApplications(), api.listOfficers()])
      .then(([appData, officerData]) => { setApps(appData); setOfficers(officerData); setError(""); })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed."));
  }, []);
  useEffect(() => { load(); }, [load]);

  const counts = useMemo(() => {
    const list = apps ?? [];
    return {
      total: list.length,
      inReview: list.filter((a) => !TERMINAL_STAGES.includes(a.current_stage)).length,
      overdue: list.filter((a) => isOverdue(a.due_at, a.current_stage)).length,
      actionRequired: list.filter((a) => a.current_stage === "CORRECTION_REQUIRED").length,
    };
  }, [apps]);

  async function assign(appId: number, officerId: number) {
    setSaving(appId);
    setError("");
    try {
      await api.assignOfficer(appId, officerId);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Assignment failed.");
    } finally {
      setSaving(null);
    }
  }

  return (
    <AppShell roles={["ADMIN"]}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">System dashboard</h1>
          <p className="mt-1 text-sm text-slate-600">System-wide counts come from live API data. No fabricated KPIs.</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard label="All applications" value={counts.total} />
          <KpiCard label="In review" value={counts.inReview} />
          <KpiCard label="Overdue" value={counts.overdue} tone="red" />
          <KpiCard label="Action required" value={counts.actionRequired} tone="amber" />
        </div>

        <div className="flex gap-2 text-sm font-semibold">
          <Link href="/admin/rules" className="rounded-lg border border-slate-300 bg-white px-4 py-2 hover:bg-slate-100">Manage compliance rules →</Link>
          <Link href="/admin/alerts" className="rounded-lg border border-slate-300 bg-white px-4 py-2 hover:bg-slate-100">Open alert centre →</Link>
        </div>

        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-lg font-bold">Officer assignment</h2>
          </div>
          {apps === null ? (
            <Spinner label="Loading applications..." />
          ) : error ? (
            <div className="p-5"><ErrorState message={error} onRetry={load} /></div>
          ) : apps.length === 0 ? (
            <EmptyState title="No applications in the system" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[44rem] text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                    <th className="px-5 py-3">Case</th>
                    <th className="px-5 py-3">Stage</th>
                    <th className="px-5 py-3">Deadline</th>
                    <th className="px-5 py-3">Assigned officer</th>
                  </tr>
                </thead>
                <tbody>
                  {apps.map((app) => (
                    <tr key={app.id} className="border-b border-slate-100">
                      <td className="px-5 py-3">
                        <p className="font-semibold">{app.title}</p>
                        <p className="text-xs text-slate-500">{app.application_code}</p>
                      </td>
                      <td className="px-5 py-3"><StageBadge stage={app.current_stage} /></td>
                      <td className="px-5 py-3 text-slate-600">{fmtDate(app.due_at)}</td>
                      <td className="px-5 py-3">
                        <select
                          value={app.assigned_officer_id ?? ""}
                          disabled={saving === app.id}
                          onChange={(e) => { if (e.target.value) void assign(app.id, Number(e.target.value)); }}
                          className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
                          <option value="">Unassigned</option>
                          {officers.map((officer) => (
                            <option key={officer.id} value={officer.id}>{officer.full_name}</option>
                          ))}
                        </select>
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
