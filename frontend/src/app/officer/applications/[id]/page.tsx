"use client";

import { AppShell } from "@/components/AppShell";
import { CaseWorkspace } from "@/components/CaseWorkspace";

export default function OfficerCasePage() {
  return (
    <AppShell roles={["OFFICER", "ADMIN"]}>
      <CaseWorkspace mode="officer" />
    </AppShell>
  );
}
