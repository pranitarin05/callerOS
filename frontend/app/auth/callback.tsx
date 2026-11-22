import { signIn } from "@supabase/auth-helpers-react"
import { useEffect } from "react"

export default function CallbackPage() {
  useEffect(() => {
    // This runs the signIn flow callback
    const { error } = supabase.auth.handleRedirectCallback({
      redirectTo: window.location.origin,
    })

    if (error) {
      console.error("Auth error:", error)
    }

    // Redirect to home after callback
    setTimeout(() => {
      window.location.href = "/"
    }, 1000)
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="bg-white rounded-lg p-8 shadow-xl text-center">
        <h2 className="text-xl font-medium mb-4">Signing in...</h2>
        <p className="text-muted-foreground">Please wait, we are redirecting you home.</p>
      </div>
    </div>
  )
}