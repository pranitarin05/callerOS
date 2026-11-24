"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type Doc = { id: string; title: string; content: string; relevance_score: number };

export default function KnowledgePage() {
  const [query, setQuery] = useState("follow up");
  const [results, setResults] = useState<Doc[]>([]);
  const [message, setMessage] = useState("Knowledge base search is available in demo mode.");

  async function search(event: React.FormEvent) {
    event.preventDefault();
    try {
      const data = await apiFetch<Doc[]>("/api/v1/conversations/knowledge-search", {
        method: "POST",
        body: JSON.stringify({ query }),
      });
      setResults(data);
      setMessage(data.length ? "" : "No matching documents.");
    } catch (err) {
      setMessage((err as Error).message);
    }
  }

  useEffect(() => {}, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Knowledge Base</h1>
        <p className="mt-1 text-sm text-slate-400">Search the configured business knowledge used by the agent.</p>
      </div>
      <Card>
        <form onSubmit={search} className="flex gap-3">
          <input className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={query} onChange={(e) => setQuery(e.target.value)} />
          <Button type="submit">Search</Button>
        </form>
        {message && <p className="mt-3 text-sm text-slate-400">{message}</p>}
      </Card>
      <div className="grid gap-4">
        {results.map((doc) => (
          <Card key={doc.id}>
            <div className="flex items-center justify-between">
              <h2 className="font-medium">{doc.title}</h2>
              <span className="text-xs text-slate-500">score {doc.relevance_score}</span>
            </div>
            <p className="mt-2 text-sm text-slate-400">{doc.content}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
