"use client";

import { useEffect, useRef, useState } from "react";
import {
  ConversationProvider,
  useConversation,
  type HookOptions,
} from "@elevenlabs/react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type AgentOverrides = {
  agent?: {
    first_message?: string;
    language?: string;
    prompt?: { prompt?: string };
  };
};

type SdkOverrides = {
  agent?: {
    firstMessage?: string;
    language?: "hi" | "en";
    prompt?: { prompt?: string };
  };
};

type SessionResponse = {
  call_id: string;
  conversation_token: string;
  agent_id: string;
  language: string;
  dynamic_variables: Record<string, string>;
  overrides: AgentOverrides | null;
};

function toSdkOverrides(overrides: AgentOverrides | null | undefined): SdkOverrides | undefined {
  if (!overrides?.agent) return undefined;
  const agent: SdkOverrides["agent"] = {};
  if (overrides.agent.first_message) agent.firstMessage = overrides.agent.first_message;
  if (overrides.agent.language === "hi" || overrides.agent.language === "en") {
    agent.language = overrides.agent.language;
  }
  if (overrides.agent.prompt?.prompt) agent.prompt = { prompt: overrides.agent.prompt.prompt };
  return agent && Object.keys(agent).length ? { agent } : undefined;
}

type Config = {
  voice_ready: boolean;
  provider: string;
  default_language: string;
};

type Message = { role: string; text: string };

function VoiceControls({ leadId, onMessage }: { leadId: string; onMessage: (message: Message) => void }) {
  const { startSession, endSession, status, mode, isSpeaking, message } = useConversation();
  const callIdRef = useRef<string | null>(null);
  const transcriptRef = useRef<string[]>([]);
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);
  const [hasMessages, setHasMessages] = useState(false);

  function record(role: string, text: string) {
    const clean = (text || "").trim();
    if (!clean) return;
    const line = `${role}: ${clean}`;
    transcriptRef.current.push(line);
    setHasMessages(true);
    onMessage({ role, text: clean });
    const id = callIdRef.current;
    if (id) {
      apiFetch(`/api/v1/voice/transcript`, {
        method: "POST",
        body: JSON.stringify({ call_id: id, text: clean, role }),
      }).catch(() => undefined);
    }
  }

  async function start() {
    setError("");
    setStarting(true);
    transcriptRef.current = [];
    try {
      const session = await apiFetch<SessionResponse>("/api/v1/voice/session", {
        method: "POST",
        body: JSON.stringify({ lead_id: leadId }),
      });
      callIdRef.current = session.call_id;
      const options: HookOptions = {
        conversationToken: session.conversation_token,
        connectionType: "webrtc",
        dynamicVariables: session.dynamic_variables,
        overrides: toSdkOverrides(session.overrides),
        onMessage: (event) => record(event.role === "user" ? "user" : "agent", event.message),
        onError: (err) => setError(String(err)),
        onDisconnect: () => {
          const id = callIdRef.current;
          if (id) {
            apiFetch("/api/v1/voice/complete", {
              method: "POST",
              body: JSON.stringify({
                call_id: id,
                transcript: transcriptRef.current.join("\n"),
                summary: "Browser voice conversation",
              }),
            }).catch(() => undefined);
          }
          callIdRef.current = null;
        },
      };
      startSession(options);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setStarting(false);
    }
  }

  function stop() {
    endSession();
  }

  const active = status === "connected" || status === "connecting";

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        {active ? (
          <Button variant="danger" onClick={stop}>End call</Button>
        ) : (
          <Button onClick={start} disabled={starting}>{starting ? "Connecting…" : "Talk to agent"}</Button>
        )}
        <span className="text-xs text-slate-500">
          status: {status} {mode ? `· ${mode}` : ""} {isSpeaking ? "· speaking" : ""}
        </span>
      </div>
      {message && !hasMessages && <p className="text-xs text-slate-500">{message}</p>}
      {error && <p className="text-sm text-rose-300">{error}</p>}
    </div>
  );
}

export function LiveVoiceAgent({ leadId }: { leadId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [config, setConfig] = useState<Config | null>(null);

  useEffect(() => {
    apiFetch<Config>("/api/v1/voice/config")
      .then(setConfig)
      .catch(() => setConfig({ voice_ready: false, provider: "elevenlabs_webrtc", default_language: "auto" }));
  }, []);

  return (
    <Card>
      <h2 className="mb-3 text-sm font-medium text-slate-300">Real-time browser voice</h2>
      {config && !config.voice_ready && (
        <p className="mb-3 text-xs text-amber-300">
          Browser voice is not configured. Set ELEVENLABS_API_KEY and an agent, then refresh.
        </p>
      )}
      <ConversationProvider>
        <VoiceControls leadId={leadId} onMessage={(item) => setMessages((prev) => [...prev, item])} />
      </ConversationProvider>
      {messages.length > 0 && (
        <div className="mt-4 max-h-64 space-y-1 overflow-y-auto rounded border border-slate-800 p-3">
          {messages.map((item, index) => (
            <p key={index} className="text-xs text-slate-300">
              <span className={item.role === "user" ? "text-sky-300" : "text-emerald-300"}>
                {item.role}:
              </span>{" "}
              {item.text}
            </p>
          ))}
        </div>
      )}
    </Card>
  );
}
