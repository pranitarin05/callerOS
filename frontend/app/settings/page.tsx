"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type AgentScript = {
  instructions: string;
  first_message: string;
  language: string;
  customized: boolean;
  defaults: {
    instructions: string;
    first_message: string;
    language: string;
  };
};

export default function SettingsPage() {
  const [config, setConfig] = useState<AgentScript | null>(null);
  const [instructions, setInstructions] = useState("");
  const [firstMessage, setFirstMessage] = useState("");
  const [language, setLanguage] = useState("auto");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiFetch<AgentScript>("/api/v1/agent-config")
      .then((data) => {
        setConfig(data);
        setInstructions(data.instructions || data.defaults.instructions || "");
        setFirstMessage(data.first_message || data.defaults.first_message || "");
        setLanguage(data.customized ? data.language : "auto");
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  async function save() {
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const saved = await apiFetch<AgentScript>("/api/v1/agent-config", {
        method: "PUT",
        body: JSON.stringify({
          instructions,
          first_message: firstMessage,
          language,
        }),
      });
      setConfig(saved);
      setMessage("Saved. This script will be used on your next call.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function reset() {
    setError("");
    setMessage("");
    try {
      await apiFetch("/api/v1/agent-config", { method: "DELETE" });
      const data = await apiFetch<AgentScript>("/api/v1/agent-config");
      setConfig(data);
      setInstructions(data.defaults.instructions);
      setFirstMessage(data.defaults.first_message);
      setLanguage("auto");
      setMessage("Reset to the ElevenLabs agent default.");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function useDefaults() {
    if (!config) return;
    setInstructions(config.defaults.instructions);
    setFirstMessage(config.defaults.first_message);
    setLanguage("auto");
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="mt-1 text-sm text-slate-400">Customize what the voice agent says on each call.</p>
      </div>

      {error && <div className="rounded-lg bg-rose-950 p-3 text-sm text-rose-200">{error}</div>}
      {message && <div className="rounded-lg bg-slate-800 p-3 text-sm text-slate-200">{message}</div>}

      <Card>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-medium text-slate-300">Agent script</h2>
            <p className="mt-1 text-xs text-slate-500">
              {config?.customized
                ? "Your custom script is active for live and browser calls."
                : "Using the ElevenLabs agent default. Save to override it."}
            </p>
          </div>
          <Button variant="ghost" onClick={useDefaults}>Use agent default</Button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-xs text-slate-500">First message</label>
            <textarea
              className="h-24 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
              value={firstMessage}
              onChange={(e) => setFirstMessage(e.target.value)}
              placeholder="Hello {{prospect_name}}, this is Sam from Caller OS..."
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-500">System prompt / instructions</label>
            <textarea
              className="h-72 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="You are Caller OS, an AI sales assistant..."
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-500">Starting language</label>
            <select
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="auto">Auto-detect caller language</option>
              <option value="en">English</option>
              <option value="hi">Hindi</option>
            </select>
            <p className="mt-1 text-xs text-slate-500">
              Auto uses the ElevenLabs language detection tool. If you force a language, the agent starts in that language but can still switch if detection is enabled.
            </p>
          </div>
          <p className="text-xs text-slate-500">
            Available variables: {"{{prospect_name}}"}, {"{{language}}"}, {"{{lead_memory}}"}, {"{{call_id}}"}, {"{{lead_id}}"}.
          </p>
          <div className="flex gap-3">
            <Button onClick={save} disabled={saving}>{saving ? "Saving…" : "Save script"}</Button>
            <Button variant="ghost" onClick={reset} disabled={!config?.customized}>Reset to default</Button>
          </div>
        </div>
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-medium text-slate-300">Runtime configuration</h2>
        {error && <div className="mb-3 text-sm text-rose-300">{error}</div>}
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between"><dt className="text-slate-500">Agent</dt><dd>{config?.defaults.language || "—"}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Custom script active</dt><dd>{config ? String(config.customized) : "—"}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Provider</dt><dd>elevenlabs_exotel / webrtc</dd></div>
        </dl>
      </Card>
    </div>
  );
}
