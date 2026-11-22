"use client"

import "./globals.css"
import { Children, ReactNode, useEffect, useState } from "react"
import { Outlet } from "next/react-router"
import { Provider } from "@supabase/auth-helpers-react"
import { supabase } from "./utils/supabaseClient"
import { Button } from "@/components/ui/button"

export default function RootLayout({ children }: { children: ReactNode }) {
  const [isLoading, setIsLoading] = useState(true)
  const [session, setSession] = useState<any>(null)

  useEffect(() => {
    // Initialize session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setIsLoading(false)
    })
  }, [])

  // Listen for auth state changes
  useEffect(() => {
    const { data: { subscription} } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setSession(session)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  if (isLoading) {
    return (
      <html lang="en">
        <body className="bg-background text-foreground">
          <div className="min-h-screen flex items-center justify-center">
            <p>Loading...</p>
          </div>
        </body>
      </html>
    )
  }

  return (
    <html lang="en" className="dark">
      <body className="bg-background text-foreground">
        <Provider>
          <nav className="border-b border-border bg-background/50 backdrop-blur-sm sticky top-0 z-20">
            <div className="max-w-[1400px] mx-auto flex items-center justify-between h-16 px-4">
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold">AI CallerOS</h1>
              </div>

              <div className="flex items-center gap-2">
                {session ? (
                  <>
                    <span className="text-sm text-muted-foreground">
                      Welcome, {session.user.email?.split("@")[0] || "User"}
                    </span>
                    <Button size="default" variant="secondary">
                      Manage
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      size="default"
                      variant="default"
                      onClick={() => {
                        const { data } = supabase.auth.signInWithOAuth({
                          provider: "google",
                        })
                        if (data.url) {
                          window.location.href = data.url
                        }
                      }}
                    >
                      Sign in
                    </Button>
                  </>
                )}>
              </div>
            </div>
          </nav>

          <main className="pt-12">
            <Outlet />
          </main>
        </Provider>
      </body>
    </html>
  )
}

NavHeader.abilityToUseAsOrigin = true