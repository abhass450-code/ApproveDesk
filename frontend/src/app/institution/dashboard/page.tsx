"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { EmptyState, ErrorState, KpiCard, Spinner, StageBadge, fmtDate, isDueSoon, isOverdue } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import type { ApplicationOut } from "@/lib/types";
import { TERMINAL_STAGES } from "@/lib/types";

export default function InstitutionDashboard() {
  const [applications, setApplications] = useState<ApplicationOut[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api.listApplications()
      .then((data) => { setApplications(data); setError(""); })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load applications."));
  }, []);
  useEffect(() => { load(); }, [load]);

  const list = applications ?? [];
  const approved = list.filter((a) => a.current_stage === "APPROVED").length;
  const actionRequired = list.filter((a) => a.current_stage === "CORRECTION_REQUIRED").length;
  const underReview = list.filter((a) => !TERMINAL_STAGES.includes(a.current_stage)).length;

  return (
    <AppShell roles={["INSTITUTION"]}>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Institution dashboard</h1>
            <p className="mt-1 text-sm text-slate-600">Track applications, deadlines, compliance outcomes and queries.</p>
          </div>
          <Link href="/institution/applications/new"
            className="inline-flex w-fit items-center rounded-lg bg-orange-600 px-5 py-3 text-sm font-bold text-white hover:bg-orange-700">
            + New Application
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard label="Total Applications" value={list.length} />
          <KpiCard label="Under Review" value={underReview} />
          <KpiCard label="Approved" value={approved} tone="green" />
          <KpiCard label="Action Required" value={actionRequired} tone="red" />
        </div>

        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-lg font-bold">Your Applications</h2>
            <p className="mt-1 text-sm text-slate-500">Live data from the API for your institution only.</p>
          </div>
          {applications === null ? (
            <Spinner label="Loading applications..." />
          ) : error ? (
            <div className="p-5"><ErrorState message={error} onRetry={load} /></div>
          ) : list.length === 0 ? (
            <EmptyState title="No applications yet" hint="Create an application to begin tracking its progress." />
          ) : (
            <div className="divide-y divide-slate-100">
              {list.map((app) => (
                <article key={app.id} className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{app.title}</h3>
                      <StageBadge stage={app.current_stage} />
                      {isOverdue(app.due_at, app.current_stage) && (
                        <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-bold text-red-700">OVERDUE</span>
                      )}
                      {!isOverdue(app.due_at, app.current_stage) && isDueSoon(app.due_at, app.current_stage) && (
                        <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-bold text-amber-800">DUE SOON</span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {app.application_code} · deadline {fmtDate(app.due_at)} · updated {fmtDate(app.updated_at)}
                    </p>
                  </div>
                  <Link href={`/institution/applications/${app.id}`} className="shrink-0 font-semibold text-orange-700 hover:underline">
                    View details →
                  </Link>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
