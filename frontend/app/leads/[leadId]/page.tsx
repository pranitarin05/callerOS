"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { LiveVoiceAgent } from "@/components/live-voice-agent";

type Lead = {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  company: string | null;
  status: string;
  interest_level: string;
  requirements: string | null;
  sentiment: string;
  call_outcome: string | null;
  next_action: string | null;
  notes: string | null;
  preferred_language: string;
  last_contact_at: string | null;
};

type Memory = {
  summary: string;
  key_facts: string[];
  language: string;
  updated_at: string | null;
};

export default function LeadDetailsPage() {
  const params = useParams<{ leadId: string }>();
  const [lead, setLead] = useState<Lead | null>(null);
  const [memory, setMemory] = useState<Memory | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<Lead>(`/api/v1/leads/${params.leadId}`)
      .then(setLead)
      .catch((err: Error) => setError(err.message));
    apiFetch<Memory>(`/api/v1/leads/${params.leadId}/memory`)
      .then(setMemory)
      .catch(() => undefined);
  }, [params.leadId]);

  async function setStatus(status: string) {
    try {
      const updated = await apiFetch<Lead>(`/api/v1/leads/${params.leadId}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      setLead(updated);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  if (error) return <div className="rounded-lg bg-rose-950 p-4 text-rose-200">{error}</div>;
  if (!lead) return <div className="text-slate-400">Loading lead…</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{lead.name}</h1>
          <p className="text-sm text-slate-400">{lead.email} {lead.company ? `· ${lead.company}` : ""}</p>
        </div>
        <Button variant="ghost" onClick={() => history.back()}>Back</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-sm font-medium text-slate-300">Profile</h2>
          <dl className="space-y-2 text-sm">
            <div><dt className="text-slate-500">Phone</dt><dd>{lead.phone || "—"}</dd></div>
            <div><dt className="text-slate-500">Status</dt><dd>{lead.status}</dd></div>
            <div><dt className="text-slate-500">Interest</dt><dd>{lead.interest_level}</dd></div>
            <div><dt className="text-slate-500">Sentiment</dt><dd>{lead.sentiment}</dd></div>
            <div><dt className="text-slate-500">Preferred language</dt><dd>{lead.preferred_language}</dd></div>
          </dl>
        </Card>
        <Card>
          <h2 className="mb-4 text-sm font-medium text-slate-300">Qualification</h2>
          <dl className="space-y-2 text-sm">
            <div><dt className="text-slate-500">Requirements</dt><dd>{lead.requirements || "—"}</dd></div>
            <div><dt className="text-slate-500">Call outcome</dt><dd>{lead.call_outcome || "—"}</dd></div>
            <div><dt className="text-slate-500">Next action</dt><dd>{lead.next_action || "—"}</dd></div>
          </dl>
        </Card>
      </div>

      <LiveVoiceAgent leadId={params.leadId} />

      <Card>
        <h2 className="mb-3 text-sm font-medium text-slate-300">Conversation memory</h2>
        {!memory?.summary ? (
          <p className="text-sm text-slate-500">No conversation memory yet. It is created after a call.</p>
        ) : (
          <>
            <p className="text-sm text-slate-300">{memory.summary}</p>
            <p className="mt-2 text-xs text-slate-500">Language: {memory.language}</p>
          </>
        )}
      </Card>

      <Card>
        <h2 className="mb-4 text-sm font-medium text-slate-300">Change status</h2>
        <div className="flex flex-wrap gap-2">
          {["new", "interested", "qualified", "not_interested"].map((status) => (
            <Button key={status} variant={lead.status === status ? "default" : "secondary"} onClick={() => setStatus(status)}>
              {status}
            </Button>
          ))}
        </div>
      </Card>
    </div>
  );
}
