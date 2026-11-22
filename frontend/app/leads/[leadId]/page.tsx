"use client"

import { useParams, useEffect, useState } from "react"
import { Card, Table, TableHeader, TableRow, TableCell } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { useSupacheck } from "@/utils/supabaseClient"

export default function LeadDetailsPage() {
  const { leadId } = useParams<{ leadId: string }>()
  const [lead, setLead] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!leadId) {
      setLoading(false)
      return
    }
    
    fetch(`/api/v1/leads/${leadId}`, {
      credentials: "include",
    })
      .then((res) => {
        if (!res.ok) throw new Error("Lead not found")
        return res.json()
      })
      .then((data) => {
        setLead(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error("Error fetching lead:", err)
        setLoading(false)
      })
  }, [leadId])

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-muted-foreground">Loading lead...</p>
      </div>
    )
  }

  if (!lead) {
    return <div className="p-8">Lead not found</div>
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-6">Lead Details</h1>
      
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Name</p>
            <p className="text-xl font-bold">{lead.name}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">Email</p>
            <p className="text-xl font-bold">{lead.email}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">Company</p>
            <p className="text-xl font-bold">{lead.company || "N/A"}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">Phone</p>
            <p className="text-xl font-bold">{lead.phone || "N/A"}</p>
          </div>
        </div>
        
        <div className="mt-6 pt-4 border-t border-border">
          <p className="text-sm font-medium text-muted-foreground">Status</p>
          <p className="text-lg font-bold">
            <span
              className={`px-2 py-1 rounded text-sm ${
                lead.status === "qualified"
                  ? "bg-green-100 text-green-800"
                  : lead.status === "new"
                    ? "bg-blue-100 text-blue-800"
                    : "bg-yellow-100 text-yellow-800"
              }`}
            >
              {lead.status}
            </span>
          </p>
          
          <p className="text-sm font-medium text-muted-foreground mt-2">Interest Level</p>
          <p className="text-lg">{lead.interest_level}</p>
          
          <p className="text-sm font-medium text-muted-foreground mt-2">Requirements</p>
          <p className="text-base">{lead.requirements || "—"}</p>
          
          <p className="text-sm font-medium text-muted-foreground mt-2">Sentiment</p>
          <p className="text-lg">{lead.sentiment}</p>
          
          <p className="text-sm font-medium text-muted-foreground mt-2">Call Outcome</p>
          <p className="text-lg">{lead.call_outcome || "—"}</p>
          
          <p className="text-sm font-medium text-muted-foreground mt-2">Next Action</p>
          <p className="text-lg">{lead.next_action || "—"}</p>
        </div>
      </Card>
      
      <Button
        onClick={() => window.history.back()}
        className="mt-4 w-full"
      >
        Back to Leads
      </Button>
    </div>
  )
}