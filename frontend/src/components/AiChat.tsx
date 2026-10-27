"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ChatMessageOut } from "@/lib/types";

interface Turn {
  role: "user" | "assistant";
  content: string;
  message?: ChatMessageOut;
}

export function AiChat({ applicationId }: { applicationId: number }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function send(event: React.FormEvent) {
    event.preventDefault();
    const question = input.trim();
    if (!question || busy) return;
    setInput("");
    setError("");
    setBusy(true);
    setTurns((prev) => [...prev, { role: "user", content: question }]);
    try {
      const response = await api.sendChatMessage(question, applicationId, conversationId ?? undefined);
      setConversationId(response.conversation_id);
      setTurns((prev) => [...prev, { role: "assistant", content: response.answer, message: response }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assistant request failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button onClick={() => setOpen(!open)}
        className="fixed bottom-5 right-5 z-40 rounded-full bg-slate-900 px-5 py-3 text-sm font-bold text-white shadow-lg hover:bg-slate-700">
        {open ? "Close assistant" : "AI Assistant"}
      </button>
      {open && (
        <div className="fixed bottom-20 right-5 z-40 flex h-[32rem] w-[22rem] flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl">
          <div className="border-b border-slate-200 px-4 py-3">
            <p className="text-sm font-bold">AI Assistant</p>
            <p className="text-xs text-slate-500">Answers only from recorded case facts. It cannot approve or reject.</p>
          </div>
          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {turns.length === 0 && (
              <p className="text-sm text-slate-500">
                Try: “Why did compliance fail?”, “Which documents are missing?”, “What should I do next?”
              </p>
            )}
            {turns.map((turn, index) => (
              <div key={index} className={`text-sm ${turn.role === "user" ? "text-right" : ""}`}>
                <div className={`inline-block max-w-full rounded-xl px-3 py-2 text-left whitespace-pre-wrap ${
                  turn.role === "user" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-800"
                }`}>
                  {turn.content}
                </div>
                {turn.message && (
                  <div className="mt-1 text-left">
                    <div className="flex flex-wrap gap-1">
                      {turn.message.sources.map((source) => (
                        <span key={`${source.type}-${source.id}`} className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[10px] text-slate-600">
                          {source.label}
                        </span>
                      ))}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {turn.message.suggested_actions.map((action) => (
                        <Link key={action.route} href={action.route} className="text-xs font-semibold text-orange-700 hover:underline">
                          {action.label} →
                        </Link>
                      ))}
                    </div>
                    <p className="mt-1 text-[10px] text-slate-400">
                      {turn.message.used_ai ? "Answer polished by AI provider; facts from records." : "Deterministic answer from records (no AI provider configured)."}
                      {turn.message.needs_human_review ? " · Needs human review." : ""}
                    </p>
                  </div>
                )}
              </div>
            ))}
            {busy && <p className="text-xs text-slate-500">Reading case records...</p>}
            {error && <p className="text-xs text-red-600">{error}</p>}
          </div>
          <form onSubmit={send} className="flex gap-2 border-t border-slate-200 p-3">
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about this case..."
              className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none" />
            <button type="submit" disabled={busy}
              className="rounded-lg bg-orange-600 px-3 py-2 text-sm font-bold text-white hover:bg-orange-700 disabled:opacity-60">
              Ask
            </button>
          </form>
        </div>
      )}
    </>
  );
}
