"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiFetch, ApiError, getToken } from "@/lib/api";

type Doc = {
  id: string;
  title: string;
  content: string;
  status: string;
  chunked: boolean;
  chunk_count: number;
  char_count: number;
  error: string | null;
  created_at: string | null;
};

type SearchHit = {
  id: string;
  title: string;
  content: string;
  relevance_score: number;
};

export default function KnowledgePage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [query, setQuery] = useState("follow up");
  const [results, setResults] = useState<SearchHit[]>([]);
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);

  const loadDocs = useCallback(() => {
    apiFetch<Doc[]>("/api/v1/knowledge/documents")
      .then(setDocs)
      .catch((err: Error) => setMessage(err.message));
  }, []);

  useEffect(() => {
    loadDocs();
  }, [loadDocs]);

  async function search(event: React.FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      const data = await apiFetch<SearchHit[]>("/api/v1/knowledge/search", {
        method: "POST",
        body: JSON.stringify({ query }),
      });
      setResults(data);
      setMessage(data.length ? "" : "No matching documents. Built-in knowledge is used by the agent as a fallback.");
    } catch (err) {
      setMessage((err as Error).message);
    }
  }

  async function upload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setMessage("");
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("title", file.name);
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
      const token = getToken();
      const response = await fetch(`${base}/api/v1/knowledge/documents/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new ApiError(body?.detail || `Upload failed (${response.status})`, response.status);
      }
      setMessage(`Uploaded ${file.name}.`);
      loadDocs();
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function remove(id: string) {
    try {
      await apiFetch(`/api/v1/knowledge/documents/${id}`, { method: "DELETE" });
      loadDocs();
    } catch (err) {
      setMessage((err as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Knowledge Base</h1>
        <p className="mt-1 text-sm text-slate-400">
          Upload documents (txt/md/pdf). They are chunked and embedded locally so the agent can answer with RAG.
        </p>
      </div>

      {message && <div className="rounded-lg bg-slate-800 p-3 text-sm text-slate-200">{message}</div>}

      <Card>
        <h2 className="mb-3 text-sm font-medium text-slate-300">Add a document</h2>
        <input
          type="file"
          accept=".txt,.md,.pdf,text/plain,application/pdf"
          onChange={upload}
          disabled={uploading}
          className="block w-full text-sm text-slate-300 file:mr-3 file:rounded file:border-0 file:bg-slate-700 file:px-3 file:py-2 file:text-slate-100"
        />
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-medium text-slate-300">Indexed documents</h2>
        {docs.length === 0 && <p className="text-sm text-slate-500">No documents yet.</p>}
        <div className="grid gap-3">
          {docs.map((doc) => (
            <div key={doc.id} className="flex items-center justify-between gap-4 rounded border border-slate-800 p-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{doc.title}</span>
                  <span className={`rounded px-2 py-0.5 text-xs ${doc.status === "ready" ? "bg-emerald-950 text-emerald-300" : "bg-rose-950 text-rose-300"}`}>
                    {doc.status}
                  </span>
                </div>
                <p className="mt-1 truncate text-xs text-slate-500">
                  {doc.chunk_count} chunks · {doc.char_count} chars
                  {doc.error ? ` · ${doc.error}` : ""}
                </p>
              </div>
              <Button variant="ghost" onClick={() => remove(doc.id)}>Delete</Button>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-medium text-slate-300">Search knowledge</h2>
        <form onSubmit={search} className="flex gap-3">
          <input
            className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Button type="submit">Search</Button>
        </form>
        <div className="mt-4 grid gap-3">
          {results.map((hit) => (
            <div key={hit.id} className="rounded border border-slate-800 p-3">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">{hit.title}</h3>
                <span className="text-xs text-slate-500">score {hit.relevance_score}</span>
              </div>
              <p className="mt-1 text-sm text-slate-400">{hit.content}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
