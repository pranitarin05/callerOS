"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHeader, TableRow } from "@/components/ui/table";
import { apiFetch } from "@/lib/api";

type Followup = {
  id: string;
  lead_id: string;
  scheduled_at: string;
  status: string;
  notes: string | null;
};

export default function FollowupsPage() {
  const [items, setItems] = useState<Followup[]>([]);
  const [leadId, setLeadId] = useState("");
  const [when, setWhen] = useState("");
  const [error, setError] = useState("");

  const load = () => apiFetch<Followup[]>("/api/v1/followups").then(setItems).catch((err: Error) => setError(err.message));

  useEffect(() => { load(); }, []);

  async function schedule(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await apiFetch("/api/v1/followups", {
        method: "POST",
        body: JSON.stringify({ lead_id: leadId, scheduled_at: new Date(when).toISOString() }),
      });
      setLeadId("");
      setWhen("");
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function complete(id: string) {
    await apiFetch(`/api/v1/followups/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "completed" }),
    });
    load();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Follow-ups</h1>
        <p className="mt-1 text-sm text-slate-400">Scheduled callbacks and next actions.</p>
      </div>

      <Card>
        <form onSubmit={schedule} className="grid gap-4 md:grid-cols-3">
          <input className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2" placeholder="Lead ID" value={leadId} onChange={(e) => setLeadId(e.target.value)} required />
          <input className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2" type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} required />
          <div><Button type="submit">Schedule</Button></div>
        </form>
        {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
      </Card>

      <Card>
        <Table>
          <TableHeader>
            <TableRow><TableCell>Lead</TableCell><TableCell>Scheduled</TableCell><TableCell>Status</TableCell><TableCell>Notes</TableCell><TableCell /></TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 && <TableRow><TableCell colSpan={5} className="text-slate-500">No follow-ups scheduled.</TableCell></TableRow>}
            {items.map((item) => (
              <TableRow key={item.id}>
                <TableCell className="font-mono text-xs">{item.lead_id.slice(0, 8)}…</TableCell>
                <TableCell>{new Date(item.scheduled_at).toLocaleString()}</TableCell>
                <TableCell>{item.status}</TableCell>
                <TableCell>{item.notes || "—"}</TableCell>
                <TableCell>{item.status === "pending" && <Button variant="ghost" onClick={() => complete(item.id)}>Complete</Button>}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
