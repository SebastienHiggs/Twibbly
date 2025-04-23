import { useUser, useSessionContext } from "@supabase/auth-helpers-react"
import { useRouter } from "next/router"
import { useEffect } from "react"
import { supabase } from "@/lib/supabaseClient"

export default function Home() {
  const router = useRouter()
  const { isLoading } = useSessionContext()
  const user = useUser()

  useEffect(() => {
    if (!isLoading && user) {
      router.push("/admin/dashboard")
    }
  }, [user, isLoading])

  const signIn = async () => {
    await supabase.auth.signInWithOAuth({ provider: "google" })
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <h1 className="text-3xl font-bold mb-6">Welcome to Twibbly</h1>
        <p className="text-gray-600 mb-6">Sign in to manage your sites and sessions.</p>
        <button
          onClick={signIn}
          className="bg-blue-600 text-white px-6 py-3 rounded font-semibold w-full"
        >
          Sign in with Google
        </button>
      </div>
    </div>
  )
}
