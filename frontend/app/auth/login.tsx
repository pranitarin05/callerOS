import { signIn } from "@supabase/auth-helpers-react"
import { useEffect } from "react"

export default function LoginPage() {
  useEffect(() => {
    // Check if user is already logged in
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        window.location.href = "/"
      }
    })
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="bg-white rounded-lg p-8 shadow-xl max-w-md w-full">
        <h2 className="text-2xl font-bold mb-6">Welcome to AI CallerOS</h2>

        <div className="space-y-4">
          <button
            onClick={() => {
              const { data } = supabase.auth.signInWithOAuth({
                provider: "google",
              })
              if (data.url) {
                window.location.href = data.url
              }
            }}
            className="w-full bg-primary text-white py-3 rounded-md hover:bg-primary/90"
          >
            Continue with Google
          </button>

          <p className="text-center text-sm text-muted-foreground">
            Or continue with email
          </p>
        </div>

        <div className="mt-6 text-center">
          <a href="/auth/callback" className="text-link">
            Continue with email magic link
          </a>
        </div>
      </div>
    </div>
  )
}