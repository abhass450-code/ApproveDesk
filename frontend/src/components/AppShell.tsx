"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import type { ReactNode } from "react";
import { useAuth, hasRole } from "@/lib/auth";
import type { Role } from "@/lib/types";
import { Spinner } from "./ui";

const NAV: Record<Role, { href: string; label: string }[]> = {
  INSTITUTION: [
    { href: "/institution/dashboard", label: "Dashboard" },
    { href: "/institution/applications/new", label: "New Application" },
  ],
  OFFICER: [{ href: "/officer/dashboard", label: "My Queue" }],
  ADMIN: [
    { href: "/admin/dashboard", label: "Dashboard" },
    { href: "/admin/rules", label: "Compliance Rules" },
    { href: "/admin/alerts", label: "Alert Centre" },
  ],
};

export function AppShell({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { user, ready, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (ready && !user) router.replace("/login");
  }, [ready, user, router]);

  if (!ready || !user) {
    return <Spinner label={ready ? "Redirecting to sign in..." : "Loading session..."} />;
  }
  if (!hasRole(user, roles)) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6 text-slate-900">
        <div className="max-w-md rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-xl font-bold">Access denied</h1>
          <p className="mt-2 text-sm text-slate-600">
            Your role ({user.role}) does not have access to this area.
          </p>
          <button onClick={logout} className="mt-5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white">
            Sign out
          </button>
        </div>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-sm font-bold text-white">A</div>
            <div>
              <p className="text-sm font-bold leading-tight">ApproveDesk</p>
              <p className="text-xs text-slate-500">Approval &amp; Compliance prototype · SIH26262</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
              Demo data
            </span>
            <div className="text-right">
              <p className="text-sm font-semibold">{user.full_name}</p>
              <p className="text-xs text-slate-500">{user.role}</p>
            </div>
            <button onClick={logout} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-semibold hover:bg-slate-100">
              Sign out
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-5 py-6 md:flex-row">
        <nav className="flex shrink-0 gap-2 md:w-52 md:flex-col">
          {NAV[user.role].map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link key={item.href} href={item.href}
                className={`rounded-lg px-4 py-2.5 text-sm font-semibold ${
                  active ? "bg-slate-900 text-white" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-100"
                }`}>
                {item.label}
              </Link>
            );
          })}
        </nav>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
