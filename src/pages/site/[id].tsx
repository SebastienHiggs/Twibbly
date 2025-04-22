import { useRouter } from "next/router"
import { useState, useEffect } from "react"
import { supabase } from "@/lib/supabaseClient"

export default function SiteAccessPage() {
  const router = useRouter()
  const { id: siteIdRaw } = router.query

  const [accessCode, setAccessCode] = useState("")
  const [submitted, setSubmitted] = useState(false)
  const [sessions, setSessions] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [siteName, setSiteName] = useState<string | null>(null)

  // Log when siteId becomes available
  useEffect(() => {
    console.log("[router.query.id]", siteIdRaw, "typeof:", typeof siteIdRaw)
  }, [siteIdRaw])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    // Ensure siteId is a string
    const siteId = typeof siteIdRaw === "string" ? siteIdRaw : null

    console.log("[handleSubmit] Access code entered:", accessCode, "typeof:", typeof accessCode)
    console.log("[handleSubmit] Site ID from query:", siteId, "typeof:", typeof siteId)

    if (!siteId) {
      console.warn("[handleSubmit] Invalid siteId — aborting")
      setError("Invalid site ID.")
      setLoading(false)
      return
    }

    const trimmedAccessCode = accessCode.trim()
    console.log("[handleSubmit] Trimmed access code:", trimmedAccessCode)

    const { data: site, error: siteError } = await supabase
        .from("sites")
        .select("id, name")
        .eq("id", siteId)
        .eq("access_code", trimmedAccessCode)
        .maybeSingle()

    console.log("[Supabase] Site query result:", site)
    console.log("[Supabase] Site query error:", siteError)

    if (siteError || !site) {
        console.warn("[handleSubmit] Site not found or access code incorrect")
        setError("Site not found or incorrect access code.")
        setLoading(false)
        return
    }

    setSiteName(site.name)  // ✅ only do this after checking it's not null

    // ✅ Fetch upcoming sessions
    const now = new Date().toISOString()
    console.log("[handleSubmit] Current timestamp:", now)

    const { data: sessionData, error: sessionError } = await supabase
      .from("sessions")
      .select("id, title, start_time")
      .eq("site_id", siteId)
      .gt("end_time", now)
      .order("start_time", { ascending: true })

    console.log("[Supabase] Sessions data:", sessionData)
    console.log("[Supabase] Sessions error:", sessionError)

    if (sessionError) {
      setError("Failed to load sessions.")
    } else {
      setSessions(sessionData || [])
      setSubmitted(true)
    }

    setLoading(false)
  }

  if (!siteIdRaw) {
    console.log("[render] Waiting for router.query.id to load...")
    return null
  }

  return (
    <div className="max-w-md mx-auto mt-10 px-4">
      <h1 className="text-2xl font-bold text-center mb-4">
        {siteName ? `Access ${siteName}` : "Access Site"}
      </h1>

      {error && <p className="text-red-600 text-center mb-3">{error}</p>}

      {!submitted ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm font-medium">Site access code:</label>
          <input
            type="text"
            value={accessCode}
            onChange={(e) => setAccessCode(e.target.value)}
            className="w-full border px-4 py-2 rounded"
            required
          />
          <button
            type="submit"
            disabled={loading || typeof siteIdRaw !== "string"}
            className="bg-blue-600 text-white w-full px-4 py-2 rounded"
          >
            {loading ? "Checking..." : "Continue"}
          </button>
        </form>
      ) : (
        <>
          <h2 className="text-xl font-semibold mt-6 mb-3">Available Sessions</h2>
          {sessions.length === 0 ? (
            <p className="text-gray-600">No upcoming sessions for this site.</p>
          ) : (
            <ul className="space-y-2">
              {sessions.map((session) => (
                <li key={session.id}>
                  <a
                    href={`/session/${session.access_code}`}
                    className="block border px-4 py-2 rounded hover:bg-gray-50"
                  >
                    <strong>{session.title || "Untitled Session"}</strong>
                    <br />
                    <span className="text-sm text-gray-600">
                      {new Date(session.start_time).toLocaleString()}
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  )
}
