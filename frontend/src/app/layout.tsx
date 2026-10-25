import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "ApproveDesk | Approval & Compliance Workflow",
  description: "A prototype for AICTE approval workflow, compliance monitoring and institutional coordination.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
