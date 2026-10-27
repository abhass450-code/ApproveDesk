"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function NewApplicationPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [applicationType, setApplicationType] = useState("NEW_PROGRAMME");
  const [academicYear, setAcademicYear] = useState("2026-27");
  const [programme, setProgramme] = useState("");
  const [facultyCount, setFacultyCount] = useState("");
  const [infrastructureCapacity, setInfrastructureCapacity] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const created = await api.createApplication({
        title: title.trim(),
        description: description.trim() || undefined,
        due_at: dueAt ? new Date(dueAt).toISOString() : undefined,
        submitted_data: {
          application_type: applicationType,
          academic_year: academicYear,
          programme: programme.trim(),
          faculty_count: Number(facultyCount),
          infrastructure_capacity: Number(infrastructureCapacity),
        },
      });
      router.push(`/institution/applications/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed.");
      setBusy(false);
    }
  }

  return (
    <AppShell roles={["INSTITUTION"]}>
      <div className="max-w-2xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-bold tracking-tight">New application</h1>
        <p className="mt-1 text-sm text-slate-600">
          Structured fields below feed the sample compliance engine. Submitting moves the case to the review workflow.
        </p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <Field label="Title"><input required value={title} onChange={(e) => setTitle(e.target.value)} className={inputCls} /></Field>
          <Field label="Description"><textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} className={inputCls} /></Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Application type">
              <select value={applicationType} onChange={(e) => setApplicationType(e.target.value)} className={inputCls}>
                <option value="NEW_PROGRAMME">New programme</option>
                <option value="EXTENSION">Extension</option>
                <option value="RENEWAL">Renewal</option>
              </select>
            </Field>
            <Field label="Academic year"><input required value={academicYear} onChange={(e) => setAcademicYear(e.target.value)} className={inputCls} /></Field>
            <Field label="Programme / course"><input required value={programme} onChange={(e) => setProgramme(e.target.value)} className={inputCls} placeholder="B.Tech Computer Science" /></Field>
            <Field label="Proposed intake (seats)"><input type="number" min={0} value={infrastructureCapacity} onChange={(e) => setInfrastructureCapacity(e.target.value)} className={inputCls} /></Field>
            <Field label="Faculty count"><input type="number" min={0} value={facultyCount} onChange={(e) => setFacultyCount(e.target.value)} className={inputCls} /></Field>
            <Field label="Target review deadline"><input type="datetime-local" value={dueAt} onChange={(e) => setDueAt(e.target.value)} className={inputCls} /></Field>
          </div>
          {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <button type="submit" disabled={busy}
            className="rounded-lg bg-orange-600 px-5 py-2.5 text-sm font-bold text-white hover:bg-orange-700 disabled:opacity-60">
            {busy ? "Submitting..." : "Submit application"}
          </button>
        </form>
      </div>
    </AppShell>
  );
}

const inputCls = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm font-semibold text-slate-700">
      {label}
      <span className="mt-1 block font-normal">{children}</span>
    </label>
  );
}
