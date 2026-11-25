"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiFetch, setSession } from "@/lib/api";

type Mode = "signin" | "signup";
type AuthResponse = {
  access_token: string;
  token_type: string;
  user: { id: string; email: string; full_name: string | null };
};

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!email.trim() || !password) return;

    setBusy(true);
    setMessage("");
    setIsError(false);

    try {
      const path = mode === "signin" ? "/api/v1/auth/login" : "/api/v1/auth/signup";
      const result = await apiFetch<AuthResponse>(path, {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });
      setSession(result.access_token, result.user.email);
      router.replace("/");
    } catch (err) {
      setIsError(true);
      setMessage(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md py-10">
      <Card>
        <h1 className="text-xl font-semibold">
          {mode === "signin" ? "Log in to Caller OS" : "Create your account"}
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          Use your email address and password. No confirmation email is needed.
        </p>

        <form onSubmit={submit} className="mt-6 space-y-4">
          <div>
            <label className="mb-1 block text-xs text-slate-400" htmlFor="email">Email</label>
            <input
              id="email"
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              type="email"
              autoComplete="email"
              placeholder="you@company.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-xs text-slate-400" htmlFor="password">Password</label>
            <input
              id="password"
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              type="password"
              autoComplete={mode === "signin" ? "current-password" : "new-password"}
              placeholder="At least 6 characters"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={6}
              required
            />
          </div>

          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? "Please wait…" : mode === "signin" ? "Log in" : "Create account"}
          </Button>
        </form>

        <div className="mt-5 text-center text-sm">
          <button
            type="button"
            className="text-indigo-400 hover:text-indigo-300"
            onClick={() => {
              setMode(mode === "signin" ? "signup" : "signin");
              setMessage("");
              setIsError(false);
            }}
          >
            {mode === "signin" ? "Need an account? Sign up" : "Already have an account? Log in"}
          </button>
        </div>

        {message && (
          <p className={`mt-4 text-sm ${isError ? "text-rose-300" : "text-amber-300"}`}>{message}</p>
        )}
      </Card>
    </div>
  );
}
