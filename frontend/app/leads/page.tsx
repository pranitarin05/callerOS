"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHeader, TableRow } from "@/components/ui/table";
import { apiFetch } from "@/lib/api";

type Lead = {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  company: string | null;
  status: string;
  interest_level: string;
  sentiment: string;
  call_outcome: string | null;
  next_action: string | null;
};

export default function LeadsPage() {
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [callMode, setCallMode] = useState<"demo" | "live">("live");
  const [form, setForm] = useState({ name: "", email: "", phone: "", company: "" });

  const load = useCallback(() => {
    const query = search ? `?search=${encodeURIComponent(search)}` : "";
    apiFetch<Lead[]>(`/api/v1/leads${query}`)
      .then(setLeads)
      .catch((err: Error) => setError(err.message));
  }, [search]);

  useEffect(() => {
    const timer = setTimeout(load, 200);
    return () => clearTimeout(timer);
  }, [load]);

  async function createLead(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await apiFetch<Lead>("/api/v1/leads", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setForm({ name: "", email: "", phone: "", company: "" });
      setShowForm(false);
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function callLead(lead: Lead) {
    setNotice("");
    setError("");
    try {
      if (!lead.phone) throw new Error("Add a phone number to this lead before calling.");
      const result = await apiFetch<{ status: string; initiation_status: string }>(
        "/api/calls/initiate",
        {
          method: "POST",
          body: JSON.stringify({
            lead_id: lead.id,
            phone_number: lead.phone,
            mode: callMode,
          }),
        },
      );
      setNotice(
        callMode === "live"
          ? `Live call submitted for ${lead.name}. Status: ${result.status}.`
          : `Demo call completed for ${lead.name}. CRM updated.`,
      );
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Leads</h1>
          <p className="mt-1 text-sm text-slate-400">Create, search, qualify and call your leads.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center rounded border border-[#1f1f23] bg-[#09090b] p-0.5">
            <button
              type="button"
              onClick={() => setCallMode("demo")}
              className={`rounded px-3 py-1 text-[11px] uppercase tracking-wide ${callMode === "demo" ? "bg-[#18181b] text-white" : "text-[#a1a1aa]"}`}
            >
              Demo
            </button>
            <button
              type="button"
              onClick={() => setCallMode("live")}
              className={`rounded px-3 py-1 text-[11px] uppercase tracking-wide ${callMode === "live" ? "bg-[#18181b] text-white" : "text-[#a1a1aa]"}`}
            >
              Live call
            </button>
          </div>
          <Button onClick={() => setShowForm((value) => !value)}>{showForm ? "Cancel" : "New lead"}</Button>
        </div>
      </div>

      {notice && <div className="rounded-lg bg-emerald-950 p-3 text-sm text-emerald-200">{notice}</div>}
      {error && <div className="rounded-lg bg-rose-950 p-3 text-sm text-rose-200">{error}</div>}

      {showForm && (
        <Card>
          <form onSubmit={createLead} className="grid gap-4 md:grid-cols-2">
            <input className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2" placeholder="Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <input className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2" placeholder="Email" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <input className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            <input className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2" placeholder="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
            <div><Button type="submit">Save lead</Button></div>
          </form>
        </Card>
      )}

      <Card>
        <input
          className="mb-4 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          placeholder="Search by name, email or company…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Table>
          <TableHeader>
            <TableRow>
              <TableCell>Name</TableCell><TableCell>Email</TableCell><TableCell>Company</TableCell>
              <TableCell>Status</TableCell><TableCell>Interest</TableCell><TableCell>Actions</TableCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {leads.length === 0 && <TableRow><TableCell colSpan={6} className="text-slate-500">No leads found.</TableCell></TableRow>}
            {leads.map((lead) => (
              <TableRow key={lead.id}>
                <TableCell className="font-medium">{lead.name}</TableCell>
                <TableCell>{lead.email}</TableCell>
                <TableCell>{lead.company || "—"}</TableCell>
                <TableCell><span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs">{lead.status}</span></TableCell>
                <TableCell>{lead.interest_level}</TableCell>
                <TableCell className="flex gap-2">
                  <Button variant="ghost" onClick={() => router.push(`/leads/${lead.id}`)}>View</Button>
                  <Button variant="secondary" onClick={() => callLead(lead)}>{callMode === "live" ? "Live call" : "Demo call"}</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
