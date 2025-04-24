import { useState } from "react"
import { useRouter } from "next/router"
import { useUser, useSessionContext } from "@supabase/auth-helpers-react"

export default function CreateOrgPage() {
  const user = useUser()
  const { supabaseClient } = useSessionContext()
  const router = useRouter()
  const [orgName, setOrgName] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const { data: sessionData } = await supabaseClient.auth.getSession()
    console.log("🧾 Insert Org session:", sessionData)

    const { data: org, error: orgError } = await supabaseClient
      .from("organisations")
      .insert({ name: orgName })
      .select("id")
      .single()

    if (orgError || !org) {
      console.error("❌ Failed org insert:", orgError)
      setError("Failed to create organisation.")
      setLoading(false)
      return
    }

    const { error: updateError } = await supabaseClient
      .from("app_users")
      .update({ organisation_id: org.id })
      .eq("id", user?.id)

    if (updateError) {
      console.error("❌ Failed to update user org:", updateError)
      setError("Failed to link organisation.")
      setLoading(false)
      return
    }

    router.push("/admin/dashboard")
  }

  return (
    <div className="max-w-md mx-auto mt-10 px-4">
      <h1 className="text-2xl font-bold mb-4 text-center">Create Your Organisation</h1>
      {error && <p className="text-red-600 text-center mb-3">{error}</p>}
      <form onSubmit={handleCreate} className="space-y-4">
        <label className="block text-sm font-medium">Organisation name:</label>
        <input
          type="text"
          value={orgName}
          onChange={(e) => setOrgName(e.target.value)}
          required
          className="w-full border px-4 py-2 rounded"
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded"
        >
          {loading ? "Creating..." : "Create Organisation"}
        </button>
      </form>
    </div>
  )
}
