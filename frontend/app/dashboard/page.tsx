"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";

type Metrics = {
  total_leads: number;
  total_calls: number;
  completed_calls: number;
  active_followups: number;
  leads_by_status: Record<string, number>;
  leads_by_interest: Record<string, number>;
  sentiment_distribution: Record<string, number>;
  recent_leads: Array<{ id: string; name: string; email: string; status: string; interest_level: string; created_at: string | null }>;
};

export default function DashboardPage() {
  const [data, setData] = useState<Metrics | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<Metrics>("/api/v1/analytics")
      .then(setData)
      .catch((err: Error) => setError(err.message));
  }, []);

  if (error) return <div className="rounded-lg bg-rose-950 p-4 text-rose-200">{error}</div>;
  if (!data) return <div className="text-slate-400">Loading dashboard…</div>;

  const statusData = Object.entries(data.leads_by_status || {}).map(([name, value]) => ({ name, value }));
  const sentimentData = Object.entries(data.sentiment_distribution || {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-400">Business metrics from your CRM.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card><p className="text-sm text-slate-400">Total leads</p><p className="mt-2 text-3xl font-bold">{data.total_leads}</p></Card>
        <Card><p className="text-sm text-slate-400">Total calls</p><p className="mt-2 text-3xl font-bold">{data.total_calls}</p></Card>
        <Card><p className="text-sm text-slate-400">Active follow-ups</p><p className="mt-2 text-3xl font-bold">{data.active_followups}</p></Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-sm font-medium text-slate-300">Leads by status</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={statusData}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" name="Leads" stroke="#818cf8" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <h2 className="mb-4 text-sm font-medium text-slate-300">Sentiment distribution</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={sentimentData}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" name="Calls" stroke="#34d399" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card>
        <h2 className="mb-4 text-sm font-medium text-slate-300">Recent leads</h2>
        <div className="space-y-2">
          {data.recent_leads.length === 0 && <p className="text-sm text-slate-500">No leads yet.</p>}
          {data.recent_leads.map((lead) => (
            <div key={lead.id} className="flex items-center justify-between rounded-lg border border-slate-800 px-4 py-2 text-sm">
              <span>{lead.name} <span className="text-slate-500">({lead.email})</span></span>
              <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs">{lead.status}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
