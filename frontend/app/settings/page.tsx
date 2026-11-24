"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type CallingConfig = {
  mode: string;
  live_ready: boolean;
  provider: string;
  agent_name: string;
  exotel_region: string;
  webhook_configured: boolean;
  webhook_secret_configured: boolean;
  groq_configured: boolean;
};

export default function SettingsPage() {
  const [config, setConfig] = useState<CallingConfig | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<CallingConfig>("/api/calls/config")
      .then(setConfig)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="mt-1 text-sm text-slate-400">Runtime configuration for the calling agent.</p>
      </div>
      {error && <div className="rounded-lg bg-rose-950 p-3 text-sm text-rose-200">{error}</div>}
      <Card>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between"><dt className="text-slate-500">Calling mode</dt><dd>{config?.mode || "unknown"}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Provider</dt><dd>{config?.provider || "elevenlabs_exotel"}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Agent</dt><dd>{config?.agent_name || "—"}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Live calling ready</dt><dd>{config ? String(config.live_ready) : "—"}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Webhook configured</dt><dd>{config ? String(config.webhook_configured) : "—"}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Webhook signature secret</dt><dd>{config ? String(config.webhook_secret_configured) : "—"}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Exotel region</dt><dd>{config?.exotel_region || "—"}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Groq analysis</dt><dd>{config ? String(config.groq_configured) : "—"}</dd></div>
        </dl>
      </Card>
    </div>
  );
}
