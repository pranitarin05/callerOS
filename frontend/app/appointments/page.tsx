"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type Lead = { id: string; name: string };
type Appointment = {
  id: string;
  lead_id: string;
  scheduled_at: string;
  duration_minutes: number;
  status: string;
  title: string;
  notes: string | null;
};

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [slots, setSlots] = useState<string[]>([]);
  const [leadId, setLeadId] = useState("");
  const [slot, setSlot] = useState("");
  const [title, setTitle] = useState("Product demo");
  const [message, setMessage] = useState("");

  const load = useCallback(() => {
    apiFetch<Appointment[]>("/api/v1/appointments")
      .then(setAppointments)
      .catch((err: Error) => setMessage(err.message));
    apiFetch<Lead[]>("/api/v1/leads")
      .then((items) => {
        setLeads(items);
        if (items.length && !leadId) setLeadId(items[0].id);
      })
      .catch(() => undefined);
    apiFetch<string[]>("/api/v1/appointments/slots?days=3")
      .then((items) => {
        setSlots(items);
        if (items.length && !slot) setSlot(items[0]);
      })
      .catch(() => undefined);
  }, [leadId, slot]);

  useEffect(() => {
    load();
  }, [load]);

  async function book(event: React.FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await apiFetch("/api/v1/appointments", {
        method: "POST",
        body: JSON.stringify({ lead_id: leadId, scheduled_at: slot, title }),
      });
      setMessage("Appointment booked.");
      load();
    } catch (err) {
      setMessage((err as Error).message);
    }
  }

  async function update(id: string, status: string) {
    try {
      await apiFetch(`/api/v1/appointments/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      load();
    } catch (err) {
      setMessage((err as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Appointments</h1>
        <p className="mt-1 text-sm text-slate-400">Book demos and track scheduled callbacks.</p>
      </div>
      {message && <div className="rounded-lg bg-slate-800 p-3 text-sm text-slate-200">{message}</div>}

      <Card>
        <h2 className="mb-4 text-sm font-medium text-slate-300">Book an appointment</h2>
        <form onSubmit={book} className="grid gap-3 md:grid-cols-4">
          <select className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={leadId} onChange={(e) => setLeadId(e.target.value)}>
            {leads.length === 0 && <option value="">No leads</option>}
            {leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.name}</option>)}
          </select>
          <select className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={slot} onChange={(e) => setSlot(e.target.value)}>
            {slots.length === 0 && <option value="">No slots</option>}
            {slots.map((item) => <option key={item} value={item}>{new Date(item).toLocaleString()}</option>)}
          </select>
          <input className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={title} onChange={(e) => setTitle(e.target.value)} />
          <Button type="submit" disabled={!leadId || !slot}>Book</Button>
        </form>
      </Card>

      <Card>
        <h2 className="mb-4 text-sm font-medium text-slate-300">Scheduled</h2>
        {appointments.length === 0 && <p className="text-sm text-slate-500">No appointments yet.</p>}
        <div className="grid gap-3">
          {appointments.map((item) => (
            <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded border border-slate-800 p-3">
              <div>
                <div className="font-medium">{item.title}</div>
                <div className="text-xs text-slate-500">
                  {new Date(item.scheduled_at).toLocaleString()} · {item.duration_minutes} min · {item.status}
                </div>
                {item.notes && <div className="mt-1 text-xs text-slate-400">{item.notes}</div>}
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" onClick={() => update(item.id, "confirmed")}>Confirm</Button>
                <Button variant="ghost" onClick={() => update(item.id, "cancelled")}>Cancel</Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
