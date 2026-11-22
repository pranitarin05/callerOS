import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Table, TableHeader, TableRow, TableCell, TableBody } from "@/components/ui/table"
import { useState } from "react"

export default function HomePage() {
  const [leads, setLeads] = useState([])
  const [search, setSearch] = useState("")

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value)
  }

  // Fetch leads from API
  useEffect(() => {
    fetch("/api/v1/leads", {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => setLeads(data))
      .catch((err) => console.error("Error fetching leads:", err))
  }, [search])

  const filteredLeads = leads.filter(
    (lead) =>
      lead.name.toLowerCase().includes(search.toLowerCase()) ||
      lead.email.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">AI CallerOS - Leads</h1>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Search leads..."
          className="border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
          onChange={handleSearch}
        />
        <Button
          onClick={() => {}}
          className="ml-2 bg-primary text-white px-4 py-2 rounded"
        >
          New Lead
        </Button>
      </div>

      {filteredLeads.length === 0 && (
        <p className="mt-4 text-muted-foreground">No leads found</p>
      )}

      {filteredLeads.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Company</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Interest</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredLeads.map((lead) => (
              <TableRow key={lead.id}>
                <TableCell>{lead.name}</TableCell>
                <TableCell>{lead.email}</TableCell>
                <TableCell>{lead.company || "-"}</TableCell>
                <TableCell>
                  <span
                    className={`px-2 py-0.5 rounded text-xs ${
                      lead.status === "qualified"
                        ? "bg-green-100 text-green-800"
                        : lead.status === "new"
                          ? "bg-blue-100 text-blue-800"
                          : "bg-yellow-100 text-yellow-800"
                    }`}
                  >
                    {lead.status}
                  </span>
                </TableCell>
                <TableCell>{lead.interest_level}</TableCell>
                <TableCell>
                  <Button
                    size="default"
                    className="text-sm px-2 py-1"
                  >
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}