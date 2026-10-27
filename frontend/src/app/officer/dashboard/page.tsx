"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { EmptyState, ErrorState, KpiCard, Spinner, StageBadge, fmtDate, isDueSoon, isOverdue } from "@/components/ui";
import { api } from "@/lib/api";
import type { ApplicationOut } from "@/lib/types";
import { WORKFLOW_STAGES } from "@/lib/types";

export default function OfficerDashboard() {
  const [apps, setApps] = useState<ApplicationOut[] | null>(null);
  const [error, setError] = useState("");
  const [stageFilter, setStageFilter] = useState<string>("ALL");

  const load = useCallback(() => {
    api.listApplications()
      .then((data) => { setApps(data); setError(""); })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed."));
  }, []);
  useEffect(() => { load(); }, [load]);

  const counts = useMemo(() => {
    const list = apps ?? [];
    return {
      assigned: list.length,
      dueSoon: list.filter((a) => isDueSoon(a.due_at, a.current_stage)).length,
      overdue: list.filter((a) => isOverdue(a.due_at, a.current_stage)).length,
      awaiting: list.filter((a) => a.current_stage === "CORRECTION_REQUIRED").length,
    };
  }, [apps]);

  const visible = useMemo(() => {
    const list = (apps ?? []).filter((a) => stageFilter === "ALL" || a.current_stage === stageFilter);
    return [...list].sort((a, b) => (a.due_at ?? "9999").localeCompare(b.due_at ?? "9999"));
  }, [apps, stageFilter]);

  return (
    <AppShell roles={["OFFICER", "ADMIN"]}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">My review queue</h1>
          <p className="mt-1 text-sm text-slate-600">Cases assigned to you, sorted by nearest deadline.</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard label="Assigned to me" value={counts.assigned} />
          <KpiCard label="Due soon (48h)" value={counts.dueSoon} tone="amber" />
          <KpiCard label="Overdue" value={counts.overdue} tone="red" />
          <KpiCard label="Awaiting institution" value={counts.awaiting} tone="green" />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm font-semibold text-slate-600">
            Filter by stage
            <select value={stageFilter} onChange={(e) => setStageFilter(e.target.value)}
              className="ml-2 rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="ALL">All stages</option>
              {WORKFLOW_STAGES.map((stage) => <option key={stage} value={stage}>{stage}</option>)}
            </select>
          </label>
        </div>

        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          {apps === null ? (
            <Spinner label="Loading queue..." />
          ) : error ? (
            <div className="p-5"><ErrorState message={error} onRetry={load} /></div>
          ) : visible.length === 0 ? (
            <EmptyState title="No cases in this view" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[40rem] text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                    <th className="px-5 py-3">Case</th>
                    <th className="px-5 py-3">Stage</th>
                    <th className="px-5 py-3">Deadline</th>
                    <th className="px-5 py-3">Flag</th>
                    <th className="px-5 py-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((app) => (
                    <tr key={app.id} className="border-b border-slate-100">
                      <td className="px-5 py-3">
                        <p className="font-semibold">{app.title}</p>
                        <p className="text-xs text-slate-500">{app.application_code}</p>
                      </td>
                      <td className="px-5 py-3"><StageBadge stage={app.current_stage} /></td>
                      <td className="px-5 py-3 text-slate-600">{fmtDate(app.due_at)}</td>
                      <td className="px-5 py-3">
                        {isOverdue(app.due_at, app.current_stage) && <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-bold text-red-700">OVERDUE</span>}
                        {!isOverdue(app.due_at, app.current_stage) && isDueSoon(app.due_at, app.current_stage) && <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-bold text-amber-800">DUE SOON</span>}
                        {app.current_stage === "CORRECTION_REQUIRED" && <span className="ml-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-bold text-blue-700">ACTION REQUIRED</span>}
                      </td>
                      <td className="px-5 py-3">
                        <Link href={`/officer/applications/${app.id}`} className="font-semibold text-orange-700 hover:underline">
                          Open case →
                        </Link>
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
