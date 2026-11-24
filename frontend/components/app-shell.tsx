"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { clearSession, getStoredEmail } from "@/lib/api";

const links = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/leads", label: "Leads" },
  { href: "/calls", label: "Calls" },
  { href: "/followups", label: "Follow-ups" },
  { href: "/knowledge", label: "Knowledge" },
  { href: "/settings", label: "Settings" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(() => getStoredEmail());

  function signOut() {
    clearSession();
    setEmail(null);
    router.push("/auth/login");
  }

  return (
    <div className="min-h-screen bg-[#09090b]">
      <header className="sticky top-0 z-20 border-b border-[#1f1f23] bg-[#09090b]/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between px-6">
          <div className="flex items-center gap-10">
            <Link href="/" className="font-display text-[17px] font-semibold text-white">
              AI CallerOS
            </Link>
            <nav className="hidden items-center gap-1 md:flex">
              {links.map((link) => {
                const active = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`rounded px-3 py-2 text-[13px] transition-colors ${
                      active ? "bg-[#18181b] text-white" : "text-[#a1a1aa] hover:text-white"
                    }`}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            {email ? (
              <>
                <span className="hidden text-[13px] text-[#a1a1aa] lg:inline">{email}</span>
                <Button variant="ghost" className="h-9 px-3" onClick={signOut}>Sign out</Button>
              </>
            ) : (
              <Link href="/auth/login">
                <Button className="h-9 px-4 text-[13px]">Log in</Button>
              </Link>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-[1440px] px-6 py-10">{children}</main>
    </div>
  );
}
