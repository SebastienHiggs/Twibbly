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
      const { data: sessionData, error: sessionError } = await supabase.auth.getSession();
      console.log("🧪 [Auth Debug] Session user ID:", sessionData?.session?.user?.id);
      console.log("🧪 [Auth Debug] Supabase token:", sessionData?.session?.access_token);

      const { data: { user: authUser }, error: authError } = await supabase.auth.getUser()

      if (authError || !authUser) {
        console.warn("❌ No auth session yet")
        return
      }

      // 🔍 Debug log to ensure matching
      console.log("🧠 Supabase Auth User:", authUser.id, authUser.email)
      console.log("🧠 useUser hook User:", user?.id, user?.email)

      if (!authUser.email || inserted) {
        console.warn("🔁 Skipping insert: email missing or already inserted")
        return
      }

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
