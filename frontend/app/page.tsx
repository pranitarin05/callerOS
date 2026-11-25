"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

type Mode = "demo" | "live";

type Lead = { id: string; name: string; phone: string | null; email: string; status: string };

type Insights = {
  call: {
    id: string;
    status: string;
    conversation_id: string | null;
    exotel_call_sid: string | null;
    initiation_status: string;
    error_message: string | null;
    duration_seconds: number | null;
  };
  live_transcript: string | null;
  transcript: { content: string } | null;
  summary: { summary: string; sentiment: string; call_outcome: string; next_action: string | null } | null;
  qualification: {
    lead_status: string;
    interest: string;
    requirements: string;
    sentiment: string;
    call_outcome: string;
    next_action: string;
  } | null;
};

type Metrics = { total_leads: number; total_calls: number; completed_calls: number; active_followups: number };

type CallingConfig = {
  mode: string;
  live_ready: boolean;
  demo_ready: boolean;
  agent_id_configured: boolean;
  phone_number_configured: boolean;
  webhook_configured: boolean;
  webhook_secret_configured: boolean;
  provider: string;
  agent_name: string;
  exotel_region: string;
  groq_configured: boolean;
};

const WAVE_BARS = Array.from({ length: 60 }, (_, index) => 10 + ((index * 17) % 38));

function Icon({ name, className = "text-[18px]" }: { name: string; className?: string }) {
  return <span className={`material-symbols-outlined ${className}`}>{name}</span>;
}

export default function HomePage() {
  const [mode, setMode] = useState<Mode>("live");
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [callingConfig, setCallingConfig] = useState<CallingConfig | null>(null);
  const [callId, setCallId] = useState<string | null>(null);
  const [insights, setInsights] = useState<Insights | null>(null);
  const [active, setActive] = useState(false);
  const [busy, setBusy] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<Lead[]>("/api/v1/leads").then(setLeads).catch(() => {});
    apiFetch<Metrics>("/api/v1/analytics").then(setMetrics).catch(() => {});
    apiFetch<CallingConfig>("/api/calls/config").then(setCallingConfig).catch(() => {});
  }, []);

  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => setElapsed((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, [active]);

  useEffect(() => {
    if (!callId || !active) return;
    const poll = setInterval(() => {
      apiFetch<Insights>(`/api/v1/calls/${callId}/insights`)
        .then((data) => {
          setInsights(data);
          if (data.call.status === "completed" || data.call.status === "failed") setActive(false);
        })
        .catch(() => {});
    }, 2000);
    return () => clearInterval(poll);
  }, [callId, active]);

  async function refreshInsights(id: string) {
    const data = await apiFetch<Insights>(`/api/v1/calls/${id}/insights`);
    setInsights(data);
    return data;
  }

  async function startCall() {
    setError("");
    setBusy(true);
    try {
      let leadId = selectedLeadId;
      let targetPhone = phone.trim();

      if (!leadId) {
        if (!targetPhone) throw new Error("Enter a phone number or select a lead.");
        const digits = targetPhone.replace(/\D/g, "") || "unknown";
        const created = await apiFetch<Lead>("/api/v1/leads", {
          method: "POST",
          body: JSON.stringify({
            name: name.trim() || "Phone Lead",
            email: `phone-${digits}@calleros.local`,
            phone: targetPhone,
            source: mode === "live" ? "elevenlabs_exotel" : "demo",
          }),
        });
        leadId = created.id;
        setLeads((current) => [created, ...current]);
        setSelectedLeadId(created.id);
      } else {
        const selected = leads.find((lead) => lead.id === selectedLeadId);
        targetPhone = selected?.phone || targetPhone;
      }

      const result = await apiFetch<{ call_id: string; status: string; initiation_status: string }>(
        "/api/calls/initiate",
        {
          method: "POST",
          body: JSON.stringify({ lead_id: leadId, phone_number: targetPhone, mode }),
        },
      );

      setCallId(result.call_id);
      setElapsed(0);
      const data = await refreshInsights(result.call_id);
      setActive(mode === "live" && data.call.status !== "completed" && data.call.status !== "failed");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start call.");
    } finally {
      setBusy(false);
    }
  }

  async function stopMonitoring() {
    if (!callId) return;
    setActive(false);
    await refreshInsights(callId);
  }

  const transcript = insights?.live_transcript?.trim() || insights?.transcript?.content || "";
  const lastLine = transcript.split("\n").filter(Boolean).slice(-1)[0] || "Agent listening — waiting for speech…";
  const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const seconds = String(elapsed % 60).padStart(2, "0");

  return (
    <div className="space-y-12">
      <section className="flex flex-col items-start gap-6">
        <div className="inline-flex items-center gap-2 rounded-full bg-[#1a1b22] px-4 py-1 text-[11px] font-medium uppercase tracking-[0.12em] text-[#a1a1aa]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#fafafa]" />
          Autonomous Voice Agent v1.0 • Realtime CRM Sync
        </div>
        <div className="flex max-w-4xl flex-col gap-3">
          <h1 className="font-display text-[40px] font-semibold leading-[48px] text-white md:text-[56px] md:leading-[64px]">
            Outbound voice, handled entirely by AI.
          </h1>
          <p className="max-w-2xl text-[16px] leading-[26px] text-[#a1a1aa]">
            Qualify leads, capture conversations, analyse sentiment and update your CRM automatically.
            Run a full demo without telephony credentials, or place a real call through ElevenLabs and Exotel.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4 pt-1">
          <Button onClick={startCall} disabled={busy} className="gap-2">
            <Icon name="phone_in_talk" />
            {busy ? "Starting…" : "Start Interactive Call"}
          </Button>
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 px-2 py-2 text-[13px] text-[#a1a1aa] transition-colors hover:text-white"
          >
            View API Documentation <Icon name="arrow_forward" className="text-[16px]" />
          </a>
          <div className="ml-auto flex items-center rounded border border-[#1f1f23] bg-[#09090b] p-0.5">
            <button
              onClick={() => setMode("demo")}
              className={`rounded px-4 py-1 text-[11px] font-medium uppercase tracking-[0.04em] transition-colors ${
                mode === "demo" ? "bg-[#18181b] text-white" : "text-[#a1a1aa] hover:text-white"
              }`}
            >
              Simulated Demo
            </button>
            <button
              onClick={() => setMode("live")}
              className={`rounded px-4 py-1 text-[11px] font-medium uppercase tracking-[0.04em] transition-colors ${
                mode === "live" ? "bg-[#18181b] text-white" : "text-[#a1a1aa] hover:text-white"
              }`}
            >
              Live ElevenLabs + Exotel
            </button>
          </div>
        </div>
      </section>

      <section className="surface-panel relative overflow-hidden p-6">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-[#33343c]/20 blur-3xl" />
        <div className="relative grid gap-6 lg:grid-cols-[280px_1fr_180px] lg:items-center">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${active ? "bg-[#fafafa] animate-ping" : "bg-[#71717a]"}`} />
              <span className="font-label text-white">
                {active ? "Call Active • Awaiting webhook" : insights?.call.status === "completed" ? "Call Completed" : "Neural Engine Standby"}
              </span>
            </div>
            <div className="flex items-center gap-3 text-[12px] text-[#71717a]">
              <span className="inline-flex items-center gap-1"><Icon name="timer" className="text-[14px]" /> {minutes}:{seconds}</span>
              <span>•</span>
              <span>{mode === "live" ? "Live telephony" : "Simulated conversation"}</span>
            </div>
          </div>

          <div className="rounded-lg border border-[#1f1f23] bg-[#09090b]/80 p-3">
            <div className={`flex h-16 items-center justify-center gap-[3px] ${active ? "wave-active" : ""}`}>
              {WAVE_BARS.map((height, index) => (
                <span
                  key={index}
                  className="wave-bar w-[3px] rounded-sm bg-[#fafafa]"
                  style={{ height, animationDelay: `${(index % 12) * 0.07}s` }}
                />
              ))}
            </div>
            <div className="mt-3 flex items-start gap-3 rounded border border-[#1f1f23] bg-[#121215]/60 p-3">
              <Icon name="forum" className="mt-0.5 text-[#71717a]" />
              <div className="flex-1">
                <div className="font-label text-[#71717a]">Realtime Transcription Stream</div>
                <p className="mt-1 text-[14px] italic text-[#c8c5ca]">{lastLine}</p>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end gap-3">
            {active && <Button variant="danger" onClick={stopMonitoring} className="w-full">Stop monitoring</Button>}
            <div className="text-right">
              <div className="font-label text-[#71717a]">Protocol</div>
              <div className="text-[16px] text-white">{mode === "live" ? "ElevenLabs / Exotel" : "Local simulator"}</div>
            </div>
          </div>
        </div>

        <div className="relative mt-6 grid gap-4 border-t border-[#1f1f23] pt-6 md:grid-cols-[1fr_1fr_1fr_auto]">
          <div>
            <label className="font-label mb-1 block text-[#71717a]">Existing lead</label>
            <select
              value={selectedLeadId}
              onChange={(event) => {
                const id = event.target.value;
                setSelectedLeadId(id);
                const selected = leads.find((lead) => lead.id === id);
                setPhone(selected?.phone || "");
                setName(selected?.name || "");
              }}
              className="h-10 w-full rounded border border-[#27272a] bg-[#09090b] px-3 text-[13px] text-white"
            >
              <option value="">New phone number…</option>
              {leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.name} — {lead.phone || lead.email}</option>)}
            </select>
          </div>
          <div>
            <label className="font-label mb-1 block text-[#71717a]">Prospect name</label>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Jane Doe"
              className="h-10 w-full rounded border border-[#27272a] bg-[#09090b] px-3 text-[13px] text-white placeholder:text-[#71717a]"
            />
          </div>
          <div>
            <label className="font-label mb-1 block text-[#71717a]">Phone number (E.164)</label>
            <input
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              placeholder="+15551234567"
              className="h-10 w-full rounded border border-[#27272a] bg-[#09090b] px-3 text-[13px] text-white placeholder:text-[#71717a]"
            />
          </div>
          <div className="flex items-end">
            <Button onClick={startCall} disabled={busy || active} variant="secondary" className="w-full">
              {mode === "live" ? "Call now • LIVE" : "Call now • DEMO"}
            </Button>
          </div>
        </div>

        {mode === "live" && callingConfig && (
          <div className="relative mt-4 space-y-2">
            {!callingConfig.live_ready && (
              <p className="text-[12px] text-[#ffb4ab]">
                Live calling needs ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID and ELEVENLABS_PHONE_NUMBER_ID in .env.
              </p>
            )}
            {!callingConfig.webhook_configured && (
              <p className="text-[12px] text-[#ffb4ab]">
                  Post-call webhook is not active. Set ELEVENLABS_WEBHOOK_URL and ELEVENLABS_WEBHOOK_SECRET in .env, then restart the backend.
              </p>
            )}
          </div>
        )}
        {error && <p className="relative mt-4 text-[12px] text-[#ffb4ab]">{error}</p>}
        {insights?.call.error_message && (
          <p className="relative mt-4 text-[12px] text-[#ffb4ab]">
            Provider error: {insights.call.error_message}
          </p>
        )}

        {insights?.qualification && (
          <div className="relative mt-6 grid gap-4 border-t border-[#1f1f23] pt-6 md:grid-cols-4">
            <div><div className="font-label text-[#71717a]">Lead status</div><div className="text-[16px] text-white">{insights.qualification.lead_status}</div></div>
            <div><div className="font-label text-[#71717a]">Sentiment</div><div className="text-[16px] text-white">{insights.qualification.sentiment}</div></div>
            <div><div className="font-label text-[#71717a]">Outcome</div><div className="text-[16px] text-white">{insights.qualification.call_outcome}</div></div>
            <div><div className="font-label text-[#71717a]">Next action</div><div className="text-[14px] text-white">{insights.qualification.next_action}</div></div>
          </div>
        )}
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        {[
          { value: String(metrics?.total_leads ?? 0), label: "Leads in CRM", note: "Owned by your account" },
          { value: String(metrics?.completed_calls ?? 0), label: "Completed calls", note: "Demo and live sessions" },
          { value: String(metrics?.active_followups ?? 0), label: "Active follow-ups", note: "Scheduled next actions" },
        ].map((item) => (
          <div key={item.label} className="surface-panel p-6 transition-colors hover:bg-[#18181b]">
            <div className="font-display text-[36px] font-semibold text-white">{item.value}</div>
            <div className="mt-1 text-[15px] font-medium text-white">{item.label}</div>
            <p className="mt-1 text-[13px] text-[#71717a]">{item.note}</p>
          </div>
        ))}
      </section>

      <section>
        <div className="mb-6 flex flex-col justify-between gap-3 md:flex-row md:items-end">
          <div>
            <div className="font-label text-[#71717a]">The calling protocol</div>
            <h2 className="font-display mt-1 text-[28px] font-semibold text-white md:text-[36px]">Autonomous execution cycle</h2>
          </div>
          <p className="max-w-md text-[14px] leading-[22px] text-[#a1a1aa]">
            From phone number to structured qualification, each step is validated and persisted.
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {[
            { n: "01", icon: "sensors", title: "Connect & Signal", body: "Enter a phone number or select a lead. ElevenLabs dials through your imported Exotel number.", foot: "Handshake", value: "Exotel" },
            { n: "02", icon: "record_voice_over", title: "Converse & Qualify", body: "The AI assistant introduces itself, checks availability, discovers requirements and handles opt-outs.", foot: "Conversation", value: "Structured" },
            { n: "03", icon: "task_alt", title: "Close & Synchronize", body: "Transcript, summary, sentiment, outcome and next action are written back to your CRM.", foot: "Sync", value: "Database" },
          ].map((step) => (
            <div key={step.n} className="surface-panel p-6">
              <div className="mb-6 flex items-center justify-between">
                <span className="font-display text-[36px] font-semibold text-[#3f3f46]">{step.n}</span>
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#1a1b22] text-white"><Icon name={step.icon} className="text-[16px]" /></span>
              </div>
              <h3 className="text-[20px] font-medium text-white">{step.title}</h3>
              <p className="mt-2 text-[14px] leading-[22px] text-[#a1a1aa]">{step.body}</p>
              <div className="mt-6 flex items-center justify-between rounded bg-[#09090b]/60 p-3 text-[12px] text-[#71717a]">
                <span>{step.foot}</span><span className="font-mono text-white">{step.value}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-[#1f1f23] bg-[#09090b] p-10">
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
          <div className="max-w-xl">
            <div className="font-label text-[#71717a]">Realtime engine</div>
            <h3 className="font-display mt-1 text-[28px] font-semibold text-white">Deploy your company&apos;s voice agent.</h3>
            <p className="mt-2 text-[14px] leading-[22px] text-[#a1a1aa]">
              Import your Exotel number into ElevenLabs, set a public webhook URL, then call any prospect from this console.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link href="/dashboard"><Button className="w-full sm:w-auto">Open Dashboard</Button></Link>
            <Link href="/auth/login"><Button variant="secondary" className="w-full sm:w-auto">Log in</Button></Link>
          </div>
        </div>
      </section>
    </div>
  );
}
