const workflow = [
  "Submitted",
  "Initial scrutiny",
  "Document verification",
  "Compliance check",
  "Officer review",
  "Inspection",
  "Final review",
];

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-950 text-lg font-bold text-white">A</div>
            <div>
              <p className="text-lg font-bold tracking-tight">ApproveDesk</p>
              <p className="text-xs text-slate-500">Approval & Compliance Workspace</p>
            </div>
          </div>
          <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">Prototype</span>
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl gap-10 px-6 py-16 md:grid-cols-[1.15fr_0.85fr] md:items-center md:py-24">
        <div>
          <p className="mb-4 text-sm font-bold uppercase tracking-[0.18em] text-blue-800">SIH26262 · AICTE workflow automation</p>
          <h1 className="max-w-2xl text-4xl font-bold leading-tight tracking-tight sm:text-5xl">One clear path from application to decision.</h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">A shared workspace for institutions and review teams to track applications, documents, compliance checks, queries and decisions with a traceable history.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a href="/login" className="rounded-xl bg-orange-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-orange-700">Sign in to the demo</a>
            <a href="https://github.com/abhass450-code/ApproveDesk" className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-100">GitHub repository</a>
          </div>
          <p className="mt-4 text-xs text-slate-500">Demo scaffold only. No official AICTE affiliation is implied.</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-500">Approval pipeline</p>
              <h2 className="mt-1 text-xl font-bold">A reviewable process</h2>
            </div>
            <div className="rounded-lg bg-blue-50 px-3 py-2 text-sm font-bold text-blue-900">7 stages</div>
          </div>
          <ol className="mt-6 space-y-3">
            {workflow.map((stage, index) => (
              <li key={stage} className="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-950 text-xs font-bold text-white">{index + 1}</span>
                <span className="text-sm font-medium">{stage}</span>
                {index === 0 && <span className="ml-auto rounded-full bg-blue-100 px-2 py-1 text-[10px] font-bold uppercase text-blue-800">Start</span>}
              </li>
            ))}
          </ol>
          <p className="mt-5 text-xs leading-5 text-slate-500">Correction requests follow a controlled return path. Final approval or rejection remains a human-authorized action.</p>
        </div>
      </section>

      <section className="border-t border-slate-200 bg-white">
        <div className="mx-auto grid max-w-6xl gap-6 px-6 py-10 sm:grid-cols-3">
          {[
            ["Traceable workflow", "Stage history and audit events help explain what changed and who acted."],
            ["Role-aware access", "Institution users, officers and admins have distinct server-enforced permissions."],
            ["AI optional", "Core workflow is designed to operate without an external AI model."],
          ].map(([title, description]) => (
            <article key={title} className="rounded-xl border border-slate-200 p-5">
              <h3 className="font-bold">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
