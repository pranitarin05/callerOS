"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHeader, TableRow } from "@/components/ui/table";
import { apiFetch } from "@/lib/api";
import { LiveVoiceAgent } from "@/components/live-voice-agent";

type Call = {
  id: string;
  lead_id: string;
  conversation_id: string | null;
  exotel_call_sid: string | null;
  provider: string;
  initiation_status: string;
  direction: string;
  status: string;
  phone_number: string | null;
  duration_seconds: number | null;
  sentiment: string | null;
  started_at: string | null;
  ended_at: string | null;
};

type Insight = {
  live_transcript: string | null;
  transcript: { content: string } | null;
  summary: {
    summary: string;
    sentiment: string;
    interest: string;
    requirements: string | null;
    call_outcome: string | null;
    next_action: string | null;
  } | null;
  qualification: {
    lead_status: string;
    interest: string;
    requirements: string;
    sentiment: string;
    call_outcome: string;
    next_action: string;
  } | null;
};

function sentimentClass(value: string | null | undefined) {
  if (value === "positive") return "bg-emerald-950 text-emerald-300";
  if (value === "negative") return "bg-rose-950 text-rose-300";
  return "bg-slate-800 text-slate-300";
}

export default function CallsPage() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [leads, setLeads] = useState<{ id: string; name: string }[]>([]);
  const [leadId, setLeadId] = useState("");
  const [error, setError] = useState("");
  const [insights, setInsights] = useState<Record<string, Insight>>({});
  const [selected, setSelected] = useState<string | null>(null);
  const [syncing, setSyncing] = useState<string | null>(null);

  const loadCalls = useCallback(() => {
    apiFetch<Call[]>("/api/v1/calls")
      .then(setCalls)
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    loadCalls();
    apiFetch<{ id: string; name: string }[]>("/api/v1/leads")
      .then((items) => {
        setLeads(items);
        if (items.length) setLeadId(items[0].id);
      })
      .catch(() => undefined);
  }, [loadCalls]);

  async function toggleInsights(callId: string) {
    if (selected === callId) {
      setSelected(null);
      return;
    }
    setSelected(callId);
    if (insights[callId]) return;
    try {
      const data = await apiFetch<Insight>(`/api/v1/calls/${callId}/insights`);
      setInsights((prev) => ({ ...prev, [callId]: data }));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function syncCall(callId: string) {
    setSyncing(callId);
    setError("");
    try {
      await apiFetch(`/api/v1/calls/${callId}/sync`, { method: "POST" });
      const data = await apiFetch<Insight>(`/api/v1/calls/${callId}/insights`);
      setInsights((prev) => ({ ...prev, [callId]: data }));
      loadCalls();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSyncing(null);
    }
  }

  const selectedInsight = selected ? insights[selected] : undefined;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Calls</h1>
        <p className="mt-1 text-sm text-slate-400">Call history, sentiment analysis and insights.</p>
      </div>
      {error && <div className="rounded-lg bg-rose-950 p-3 text-sm text-rose-200">{error}</div>}
      {leadId && (
        <div>
          <label className="mb-2 block text-sm text-slate-400">Start a browser voice session</label>
          <select
            className="mb-3 rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            value={leadId}
            onChange={(e) => setLeadId(e.target.value)}
          >
            {leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.name}</option>)}
          </select>
          <LiveVoiceAgent leadId={leadId} />
        </div>
      )}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableCell>Lead</TableCell><TableCell>Status</TableCell><TableCell>Phone</TableCell>
              <TableCell>Duration</TableCell><TableCell>Sentiment</TableCell><TableCell>Started</TableCell>
              <TableCell>Provider ID</TableCell><TableCell>Actions</TableCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {calls.length === 0 && <TableRow><TableCell colSpan={8} className="text-slate-500">No calls yet. Start a demo call from the Leads page.</TableCell></TableRow>}
            {calls.map((call) => (
              <TableRow key={call.id}>
                <TableCell className="font-mono text-xs">{call.lead_id.slice(0, 8)}…</TableCell>
                <TableCell>{call.status}</TableCell>
                <TableCell>{call.phone_number || "—"}</TableCell>
                <TableCell>{call.duration_seconds ? `${call.duration_seconds}s` : "—"}</TableCell>
                <TableCell>
                  <span className={`rounded px-2 py-0.5 text-xs ${sentimentClass(call.sentiment)}`}>
                    {call.sentiment || "pending"}
                  </span>
                </TableCell>
                <TableCell>{call.started_at ? new Date(call.started_at).toLocaleString() : "—"}</TableCell>
                <TableCell className="font-mono text-xs">
                  {call.exotel_call_sid || call.conversation_id || call.provider}
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button variant="secondary" onClick={() => toggleInsights(call.id)}>
                      {selected === call.id ? "Hide" : "Insights"}
                    </Button>
                    {call.conversation_id && (
                      <Button variant="ghost" onClick={() => syncCall(call.id)} disabled={syncing === call.id}>
                        {syncing === call.id ? "Syncing…" : "Sync"}
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {selected && (
        <Card>
          <h2 className="mb-4 text-sm font-medium text-slate-300">Call insights</h2>
          {!selectedInsight ? (
            <p className="text-sm text-slate-500">Loading insights…</p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-400">Sentiment</span>
                  <span className={`rounded px-2 py-0.5 text-xs ${sentimentClass(selectedInsight.qualification?.sentiment || selectedInsight.summary?.sentiment)}`}>
                    {selectedInsight.qualification?.sentiment || selectedInsight.summary?.sentiment || "pending"}
                  </span>
                </div>
                <p className="text-sm text-slate-300">
                  <span className="text-slate-500">Interest: </span>
                  {selectedInsight.qualification?.interest || selectedInsight.summary?.interest || "—"}
                </p>
                <p className="text-sm text-slate-300">
                  <span className="text-slate-500">Outcome: </span>
                  {selectedInsight.qualification?.call_outcome || selectedInsight.summary?.call_outcome || "—"}
                </p>
                <p className="text-sm text-slate-300">
                  <span className="text-slate-500">Next action: </span>
                  {selectedInsight.qualification?.next_action || selectedInsight.summary?.next_action || "—"}
                </p>
                <p className="text-sm text-slate-300">
                  <span className="text-slate-500">Requirements: </span>
                  {selectedInsight.qualification?.requirements || selectedInsight.summary?.requirements || "—"}
                </p>
                <div className="rounded border border-slate-800 p-3">
                  <h3 className="text-xs text-slate-500">Summary</h3>
                  <p className="mt-1 text-sm text-slate-300">
                    {selectedInsight.summary?.summary || "No summary yet."}
                  </p>
                </div>
              </div>
              <div className="rounded border border-slate-800 p-3">
                <h3 className="text-xs text-slate-500">Transcript</h3>
                <pre className="mt-1 max-h-72 overflow-y-auto whitespace-pre-wrap text-xs text-slate-300">
                  {selectedInsight.transcript?.content || selectedInsight.live_transcript || "No transcript yet."}
                </pre>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
