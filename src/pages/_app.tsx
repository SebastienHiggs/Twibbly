import { AppProps } from "next/app"
import { SessionContextProvider, useUser } from "@supabase/auth-helpers-react"
import { supabase } from "@/lib/supabaseClient"
import { useEffect, useState } from "react"
import "@/styles/globals.css"

function InsertUserIfNeeded() {
  const user = useUser()
  const [inserted, setInserted] = useState(false)

  useEffect(() => {
    const insertUser = async () => {
      const { data: { user: authUser }, error: authError } = await supabase.auth.getUser()
  
      // Require both to be ready
      if (!authUser?.id || !user?.id || authUser.id !== user.id || inserted) {
        console.warn("🔁 Skipping insert — user not ready or already inserted")
        return
      }
  
      console.log("✅ Auth + Hook user match:", authUser.id)
  
      type UserRole = "super_admin" | "org_admin" | "org_user" | "user"

      const { error: insertError } = await supabase
        .from("app_users")
        .upsert({
          id: authUser.id, // ✅ this matches auth.uid()
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
  }, [user, inserted])

  return null
}

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <SessionContextProvider supabaseClient={supabase}>
      <InsertUserIfNeeded />
      <Component {...pageProps} />
    </SessionContextProvider>
  )
}
