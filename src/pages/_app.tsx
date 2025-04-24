// pages/_app.tsx
import { AppProps } from "next/app"
import {
  SessionContextProvider,
  useUser,
  useSessionContext,
} from "@supabase/auth-helpers-react"
import { createPagesBrowserClient } from "@supabase/auth-helpers-nextjs"
import { useEffect, useState } from "react"
import { useRouter } from "next/router"
import "@/styles/globals.css"

function InsertUserIfNeeded() {
  const { supabaseClient } = useSessionContext()
  const user = useUser()
  const [inserted, setInserted] = useState(false)

  useEffect(() => {
    const insertUser = async () => {
      const { data: { user: authUser }, error: authError } = await supabaseClient.auth.getUser()

      if (!authUser?.id || !user?.id || authUser.id !== user.id || inserted) {
        console.warn("🔁 Skipping insert — user not ready or already inserted")
        return
      }

      console.log("✅ Auth + Hook user match:", authUser.id)

      type UserRole = "super_admin" | "org_admin" | "org_user" | "user"

      const { error: insertError } = await supabaseClient
        .from("app_users")
        .upsert({
          id: authUser.id,
          email: authUser.email,
          role: "org_admin" as UserRole,
          created_at: new Date().toISOString(),
          organisation_id: null,
        })

      if (insertError) {
        console.error("❌ Failed to insert user:", insertError.message)
      } else {
        console.log("✅ User inserted into app_users")
        setInserted(true)
      }
    }

    insertUser()
  }, [inserted, user, supabaseClient])

  return null
}

function OrgRedirectGuard() {
  const user = useUser()
  const { supabaseClient } = useSessionContext()
  const router = useRouter()

  useEffect(() => {
    const checkOrg = async () => {
      if (!user) return
      const { data, error } = await supabaseClient
        .from("app_users")
        .select("role, organisation_id")
        .eq("id", user.id)
        .maybeSingle()

      if (data?.role === "org_admin" && !data?.organisation_id) {
        router.push("/admin/create-org")
      }
    }

    checkOrg()
  }, [user, supabaseClient])

  return null
}

export default function MyApp({ Component, pageProps }: AppProps) {
  const [supabaseClient] = useState(() => createPagesBrowserClient())

  return (
    <SessionContextProvider supabaseClient={supabaseClient}>
      <InsertUserIfNeeded />
      <OrgRedirectGuard />
      <Component {...pageProps} />
    </SessionContextProvider>
  )
}
