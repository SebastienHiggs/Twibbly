import { useRouter } from "next/router"
import { useState } from "react"
import { supabase } from "@/lib/supabaseClient"

export default function SiteAccessPage() {
  const router = useRouter()
  const { id: siteId } = router.query

  const [accessCode, setAccessCode] = useState("")
  const [submitted, setSubmitted] = useState(false)
  const [sessions, setSessions] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    if (!siteId) return

    // Validate site and access code in one go
    const { data: site, error: siteError } = await supabase
      .from("sites")
      .select("id")
      .eq("id", siteId)
      .eq("access_code", accessCode)
      .maybeSingle()

    if (siteError || !site) {
      setError("Site not found or incorrect access code.")
      setLoading(false)
      return
    }

    // Fetch upcoming sessions
    const now = new Date().toISOString()
    const { data: sessionData, error: sessionError } = await supabase
      .from("sessions")
      .select("id, title, start_time, access_code")
      .eq("site_id", siteId)
      .gt("end_time", now)
      .order("start_time", { ascending: true })

    if (sessionError) {
      setError("Failed to load sessions.")
    } else {
      setSessions(sessionData)
      setSubmitted(true)
    }

    setLoading(false)
  }

  if (!siteId) return null

  return (
    <div className="max-w-md mx-auto mt-10 px-4">
      <h1 className="text-2xl font-bold text-center mb-4">Access Site</h1>

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
            disabled={loading}
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
