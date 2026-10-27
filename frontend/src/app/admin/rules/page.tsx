"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { EmptyState, SeverityBadge, Spinner } from "@/components/ui";
import { api } from "@/lib/api";
import type { ComplianceRuleOut, Severity } from "@/lib/types";

const EMPTY_FORM = { code: "", name: "", field_key: "", operator: ">=", threshold_value: "", unit: "", severity: "MEDIUM" as Severity, description: "" };

export default function AdminRulesPage() {
  const [rules, setRules] = useState<ComplianceRuleOut[] | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editing, setEditing] = useState<ComplianceRuleOut | null>(null);
  const [editThreshold, setEditThreshold] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.listComplianceRules()
      .then((data) => { setRules(data); setError(""); })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed."));
  }, []);
  useEffect(() => { load(); }, [load]);

  async function createRule(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await api.createComplianceRule({
        code: form.code.trim(), name: form.name.trim(), field_key: form.field_key.trim(),
        operator: form.operator, threshold_value: form.operator === "exists" ? null : Number(form.threshold_value),
        unit: form.unit.trim() || null, severity: form.severity, demo_only: true,
        description: form.description.trim() || null,
      });
      setForm(EMPTY_FORM);
      setNotice("Rule created. It is labelled DEMO ONLY until verified against an official source.");
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create failed.");
    } finally {
      setBusy(false);
    }
  }

  async function saveEdit(rule: ComplianceRuleOut) {
    setBusy(true);
    setError("");
    try {
      await api.updateComplianceRule(rule.id, { threshold_value: Number(editThreshold) });
      setEditing(null);
      setNotice(`Rule ${rule.code} updated to a new version. Old results stay traceable to earlier versions.`);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function toggleActive(rule: ComplianceRuleOut) {
    await api.updateComplianceRule(rule.id, { active: !rule.active }).then(load)
      .catch((e) => setError(e instanceof Error ? e.message : "Update failed."));
  }

  return (
    <AppShell roles={["ADMIN"]}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Compliance rules</h1>
          <p className="mt-1 text-sm text-slate-600">
            Configurable sample rules. Thresholds are demo assumptions, not official AICTE requirements, until verified against an official source.
          </p>
        </div>

        {notice && <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</p>}
        {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}

        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-bold">Create sample rule</h2>
          <form onSubmit={createRule} className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <input required placeholder="Code (e.g. DEMO-FACULTY-002)" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className={cls} />
            <input required placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={cls} />
            <input required placeholder="field_key (e.g. faculty_count)" value={form.field_key} onChange={(e) => setForm({ ...form, field_key: e.target.value })} className={cls} />
            <select value={form.operator} onChange={(e) => setForm({ ...form, operator: e.target.value })} className={cls}>
              <option value=">=">&gt;=</option><option value="<=">&lt;=</option>
              <option value="==">==</option><option value="!=">!=</option><option value="exists">exists</option>
            </select>
            {form.operator !== "exists" && (
              <input required type="number" placeholder="Threshold" value={form.threshold_value} onChange={(e) => setForm({ ...form, threshold_value: e.target.value })} className={cls} />
            )}
            <input placeholder="Unit (e.g. faculty members)" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} className={cls} />
            <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value as Severity })} className={cls}>
              <option value="LOW">LOW</option><option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option><option value="CRITICAL">CRITICAL</option>
            </select>
            <input placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className={cls} />
            <button type="submit" disabled={busy} className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-bold text-white hover:bg-orange-700 disabled:opacity-50">
              Create rule
            </button>
          </form>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          {rules === null ? (
            <Spinner label="Loading rules..." />
          ) : rules.length === 0 ? (
            <EmptyState title="No rules configured" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[48rem] text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                    <th className="px-5 py-3">Rule</th>
                    <th className="px-5 py-3">Condition</th>
                    <th className="px-5 py-3">Severity</th>
                    <th className="px-5 py-3">Version</th>
                    <th className="px-5 py-3">Source</th>
                    <th className="px-5 py-3">State</th>
                    <th className="px-5 py-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map((rule) => (
                    <tr key={rule.id} className="border-b border-slate-100 align-top">
                      <td className="px-5 py-3">
                        <p className="font-mono text-xs font-bold">{rule.code}</p>
                        <p className="text-xs text-slate-500">{rule.name}</p>
                      </td>
                      <td className="px-5 py-3 font-mono text-xs">
                        {rule.field_key} {rule.operator} {String(rule.threshold_value ?? "")}{rule.unit ? ` ${rule.unit}` : ""}
                        {editing?.id === rule.id ? (
                          <span className="ml-2 inline-flex items-center gap-1">
                            <input type="number" value={editThreshold} onChange={(e) => setEditThreshold(e.target.value)} className="w-20 rounded border border-slate-300 px-2 py-1" />
                            <button onClick={() => saveEdit(rule)} disabled={busy} className="rounded bg-slate-900 px-2 py-1 text-xs font-bold text-white">Save</button>
                            <button onClick={() => setEditing(null)} className="rounded border border-slate-300 px-2 py-1 text-xs">Cancel</button>
                          </span>
                        ) : (
                          <button onClick={() => { setEditing(rule); setEditThreshold(String(rule.threshold_value ?? "")); }}
                            className="ml-2 text-orange-700 hover:underline">Edit</button>
                        )}
                      </td>
                      <td className="px-5 py-3"><SeverityBadge severity={rule.severity} /></td>
                      <td className="px-5 py-3 text-xs">v{rule.version}</td>
                      <td className="px-5 py-3 text-xs">
                        {rule.demo_only ? (
                          <span className="rounded-full bg-amber-50 px-2 py-0.5 font-bold text-amber-800">DEMO ONLY</span>
                        ) : (
                          <span className="text-emerald-700">Verified source</span>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <button onClick={() => toggleActive(rule)}
                          className={`rounded-full px-3 py-1 text-xs font-bold ${rule.active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                          {rule.active ? "ACTIVE" : "INACTIVE"}
                        </button>
                      </td>
                      <td className="px-5 py-3 text-xs text-slate-500">{rule.description}</td>
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

const cls = "rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none";
