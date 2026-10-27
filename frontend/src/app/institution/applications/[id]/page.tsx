"use client";

import { AppShell } from "@/components/AppShell";
import { CaseWorkspace } from "@/components/CaseWorkspace";

export default function InstitutionCasePage() {
  return (
    <AppShell roles={["INSTITUTION"]}>
      <CaseWorkspace mode="institution" />
    </AppShell>
  );
}
