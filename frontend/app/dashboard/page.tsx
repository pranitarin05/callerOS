"use client"

import { useEffect, useState } from "react"
import { Card, Table, TableHeader, TableRow, TableCell, TableBody } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { ChartContainer, ResponsiveContainer, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from "recharts"
import { useSupacheck } from "@/utils/supabaseClient"

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<{
    total_leads: number
    leads_by_status: Record<string, number>
    leads_by_interest: Record<string, number>
    total_calls: number
    completed_calls: number
    active_followups: number
    recent_leads: any[]
    calls_over_time: any
    sentiment_distribution: Record<string, number>
  } | null>(null)
  
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/api/v1/analytics/dashboard", {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => {
        setMetrics(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error("Error fetching dashboard metrics:", err)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-muted-foreground">Loading dashboard...</p>
      </div>
    )
  }

  if (!metrics) {
    return <div className="p-8">Error loading dashboard data</div>
  }

  const {
    total_leads,
    leads_by_status,
    leads_by_interest,
    total_calls,
    completed_calls,
    active_followups,
    recent_leads,
    calls_over_time,
    sentiment_distribution,
  } = metrics

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <Card>
          <h3 className="text-sm font-medium text-muted-foreground mb-2">Total Leads</h3>
          <p className="text-3xl font-bold">{total_leads}</p>
        </Card>
        
        <Card>
          <h3 className="text-sm font-medium text-muted-foreground mb-2">Total Calls</h3>
          <p className="text-3xl font-bold">{total_calls}</p>
        </Card>
        
        <Card>
          <h3 className="text-sm font-medium text-muted-foreground mb-2">Active Follow-ups</h3>
          <p className="text-3xl font-bold">{active_followups}</p>
        </Card>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Leads by Status Chart */}
        <Card>
          <h3 className="text-sm font-medium text-muted-foreground mb-3">Leads by Status</h3>
          <ChartContainer
            width={300}
            height={200>
            <ResponsiveContainer>
              <Line
                data={Object.entries(leads_by_status).map(([key, value]) => ({
                  name: key,
                  value,
                }))}
                margin={{ top: 20, right: 30, left: 0, bottom: 0 }}
                payload={{ fill: (series, ctx) => series.fill }}
                strokeWidth={2}
                activeDot={{ r: 8 }}
              >
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <CartesianGrid strokeDasharray="3 3" />
              </Line>
            </ResponsiveContainer>
          </ChartContainer>
        </Card>
        
        {/* Sentiment Distribution Chart */}
        <Card>
          <h3 className="text-sm font-medium text-muted-foreground mb-3">Sentiment Distribution</h3>
          <ChartContainer
            width={300}
            height={200}
            >
            <ResponsiveContainer>
              <Line
                data={Object.entries(sentiment_distribution).map(([key, value]) => ({
                  name: key,
                  value,
                }))}
                margin={{ top: 20, right: 30, left: 0, bottom: 0 }}
                payload={{ fill: (series, ctx) => series.fill }}
                strokeWidth={2}
                activeDot={{ r: 8 }}
              >
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <CartesianGrid strokeDasharray="3 3" />
              </Line>
            </ResponsiveContainer>
          </ChartContainer>
        </Card>
      </div>
      
      {/* Recent Leads Table */}
      <Card>
        <h3 className="text-sm font-medium text-muted-foreground mb-3">Recent Leads</h3>
        <Table>
          <TableHeader>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Interest</TableCell>
              <TableCell>Created</TableCell>
            </TableRow>
          </TableHeader>
          <TableBody>
            {recent_leads.map((lead) => (
              <TableRow key={lead.id}>
                <TableCell>{lead.name}</TableCell>
                <TableCell>{lead.email}</TableCell>
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
                  <span className="text-sm text-muted-foreground">
                    {lead.created_at ? new Date(lead.created_at).toLocaleDateString() : "N/A"}
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}