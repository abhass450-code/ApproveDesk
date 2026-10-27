"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { roleHome } from "@/lib/types";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await login(email.trim(), password);
      router.replace(roleHome(user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed.");
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-5 text-slate-900">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 font-bold text-white">A</div>
          <div>
            <h1 className="text-lg font-bold">Sign in to ApproveDesk</h1>
            <p className="text-xs text-slate-500">Approval &amp; Compliance prototype · SIH26262</p>
          </div>
        </div>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-semibold">Email</label>
            <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
              placeholder="you@example.com" />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-semibold">Password</label>
            <input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none" />
          </div>
          {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <button type="submit" disabled={busy}
            className="w-full rounded-lg bg-orange-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-orange-700 disabled:opacity-60">
            {busy ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="mt-6 rounded-lg bg-slate-50 p-4 text-xs leading-5 text-slate-600">
          <p className="font-semibold text-slate-700">Synthetic demo accounts (password for all):</p>
          <p>institution.demo@example.com · officer.demo@example.com · admin.demo@example.com</p>
          <p className="mt-1 font-mono">Demo-Only-ChangeMe-2026!</p>
        </div>
        <p className="mt-4 text-center text-xs text-slate-500">
          Prototype with fictional data. No official AICTE affiliation is implied.
        </p>
      </div>
    </main>
  );
}
