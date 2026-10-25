
"use client";

import { useEffect, useState } from "react";

type Application = {
  id: number | string;
  application_type?: string;
  course?: string;
  stage?: string;
  status?: string;
  updated_at?: string;
  created_at?: string;
};

export default function InstitutionDashboard() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadApplications() {
      try {
        const baseUrl = (
          process.env.NEXT_PUBLIC_API_BASE_URL ||
          "http://localhost:8000/api"
        ).replace(/\/$/, "");

        const response = await fetch(`${baseUrl}/applications`, {
          signal: controller.signal,
          // Authentication will be connected using the team's agreed
          // auth/token helper when that implementation is available.
        });

        if (!response.ok) {
          throw new Error(
            response.status === 401
              ? "Please sign in to view your applications."
              : `Could not load applications (${response.status}).`
          );
        }

        const data = await response.json();
        setApplications(Array.isArray(data) ? data : data.items ?? []);
      } catch (err) {
        if (err instanceof Error && err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadApplications();

    return () => controller.abort();
  }, []);

  const approved = applications.filter(
    (app) => app.stage === "APPROVED" || app.status === "APPROVED"
  ).length;

  const actionRequired = applications.filter(
    (app) =>
      app.status === "ACTION_REQUIRED" ||
      app.stage === "CORRECTION_REQUIRED"
  ).length;

  const underReview = applications.filter(
    (app) =>
      !["APPROVED", "REJECTED"].includes(app.stage ?? "") &&
      !["APPROVED", "REJECTED"].includes(app.status ?? "") &&
      app.status !== "ACTION_REQUIRED" &&
      app.stage !== "CORRECTION_REQUIRED"
  ).length;

  const summary = [
    { label: "Total Applications", value: applications.length },
    { label: "Approved", value: approved },
    { label: "Under Review", value: underReview },
    { label: "Action Required", value: actionRequired },
  ];

  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8 text-slate-900 sm:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-indigo-600">
              APPROVEDESK · INSTITUTION PORTAL
            </p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight">
              Dashboard
            </h1>
            <p className="mt-2 text-slate-600">
              Track applications and respond to pending actions.
            </p>
          </div>

          <a
            href="/institution/applications/new"
            className="inline-flex w-fit items-center rounded-lg bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700"
          >
            + New Application
          </a>
        </header>

        <section
          aria-label="Application summary"
          className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
          {summary.map((item) => (
            <div
              key={item.label}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <p className="text-sm text-slate-500">{item.label}</p>
              <p className="mt-3 text-3xl font-bold">{item.value}</p>
            </div>
          ))}
        </section>

        <section className="mt-8 rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-lg font-bold">Your Applications</h2>
            <p className="mt-1 text-sm text-slate-500">
              Application progress based on the server's current data.
            </p>
          </div>

          <div className="p-5">
            {loading ? (
              <p role="status" className="py-8 text-center text-slate-500">
                Loading applications...
              </p>
            ) : error ? (
              <div
                role="alert"
                className="rounded-lg bg-red-50 p-4 text-red-700"
              >
                <p>{error}</p>
                <p className="mt-2 text-sm">
                  Check that the backend is running and sign in when
                  authentication is connected.
                </p>
              </div>
            ) : applications.length === 0 ? (
              <div className="py-10 text-center">
                <h3 className="font-semibold">No applications yet</h3>
                <p className="mt-2 text-sm text-slate-500">
                  Create an application to begin tracking its progress.
                </p>
                <a
                  href="/institution/applications/new"
                  className="mt-4 inline-block font-semibold text-indigo-600 hover:underline"
                >
                  Create your first application
                </a>
              </div>
            ) : (
              <div className="space-y-3">
                {applications.map((app) => (
                  <article
                    key={app.id}
                    className="flex flex-col gap-3 rounded-lg border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <h3 className="font-semibold">
                        {app.application_type || app.course || "Application"}
                      </h3>
                      <p className="mt-1 text-sm text-slate-500">
                        ID: {app.id}
                      </p>
                      <p className="mt-1 text-sm text-slate-600">
                        Stage: {app.stage || "Not provided"}
                      </p>
                      {app.updated_at || app.created_at ? (
                        <p className="mt-1 text-xs text-slate-500">
                          Last updated: {app.updated_at || app.created_at}
                        </p>
                      ) : null}
                    </div>

                    <a
                      href={`/institution/applications/${app.id}`}
                      className="font-semibold text-indigo-600 hover:underline"
                    >
                      View details →
                    </a>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
