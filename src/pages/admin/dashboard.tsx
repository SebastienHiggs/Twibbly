import { useEffect, useState } from "react"
import { useRouter } from "next/router"
import { useUser, useSessionContext } from "@supabase/auth-helpers-react"
import { supabase } from "@/lib/supabaseClient"
import Link from "next/link"

export default function AdminDashboard() {
  const { isLoading } = useSessionContext()
  const user = useUser()
  const router = useRouter()

  const [sites, setSites] = useState<any[]>([])
  const [loadingSites, setLoadingSites] = useState(true)

  // 🔒 Redirect to home if not logged in
  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/")
    }
  }, [user, isLoading])

  // 🧾 Fetch sites if logged in
  useEffect(() => {
    const fetchSites = async () => {
      if (!user) return
      const { data, error } = await supabase
        .from("sites")
        .select("*")
        .eq("organisation_id", user.user_metadata?.organisation_id)

      if (error) {
        console.error("Failed to fetch sites:", error.message)
      } else {
        setSites(data || [])
      }

      setLoadingSites(false)
    }

    fetchSites()
  }, [user])

  const signOut = async () => {
    await supabase.auth.signOut()
    router.push("/")
  }

  if (isLoading || (!user && !loadingSites)) return null

  return (
    <div className="max-w-2xl mx-auto mt-10 px-4">
      <h1 className="text-2xl font-bold mb-2">Admin Dashboard</h1>
      <p className="text-sm text-gray-600 mb-6">Signed in as {user?.email}</p>

      <button
        onClick={signOut}
        className="text-sm underline text-blue-600 mb-6"
      >
        Sign out
      </button>

      <h2 className="text-xl font-semibold mb-4">Your Sites</h2>

      {loadingSites ? (
        <p>Loading sites...</p>
      ) : sites.length === 0 ? (
        <p>No sites found.</p>
      ) : (
        <ul className="space-y-3">
          {sites.map((site) => (
            <li key={site.id} className="border p-4 rounded">
              <h3 className="font-semibold">{site.name}</h3>
              <p className="text-sm text-gray-600">Site ID: {site.id}</p>
              <Link
                href={`/admin/site/${site.id}`}
                className="text-sm text-blue-600 underline"
              >
                Manage sessions →
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
