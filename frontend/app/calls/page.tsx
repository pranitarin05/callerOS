"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHeader, TableRow } from "@/components/ui/table";
import { apiFetch } from "@/lib/api";

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
  started_at: string | null;
  ended_at: string | null;
};

export default function CallsPage() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<Call[]>("/api/v1/calls")
      .then(setCalls)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Calls</h1>
        <p className="mt-1 text-sm text-slate-400">Call history from demo and live calling.</p>
      </div>
      {error && <div className="rounded-lg bg-rose-950 p-3 text-sm text-rose-200">{error}</div>}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableCell>Lead</TableCell><TableCell>Status</TableCell><TableCell>Phone</TableCell>
              <TableCell>Duration</TableCell><TableCell>Started</TableCell><TableCell>Provider ID</TableCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {calls.length === 0 && <TableRow><TableCell colSpan={6} className="text-slate-500">No calls yet. Start a demo call from the Leads page.</TableCell></TableRow>}
            {calls.map((call) => (
              <TableRow key={call.id}>
                <TableCell className="font-mono text-xs">{call.lead_id.slice(0, 8)}…</TableCell>
                <TableCell>{call.status}</TableCell>
                <TableCell>{call.phone_number || "—"}</TableCell>
                <TableCell>{call.duration_seconds ? `${call.duration_seconds}s` : "—"}</TableCell>
                <TableCell>{call.started_at ? new Date(call.started_at).toLocaleString() : "—"}</TableCell>
                <TableCell className="font-mono text-xs">
                  {call.exotel_call_sid || call.conversation_id || call.provider}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
