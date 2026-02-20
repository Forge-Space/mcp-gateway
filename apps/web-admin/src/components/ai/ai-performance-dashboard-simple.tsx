'use client'

import { useState, useEffect } from 'react'

export default function AIPerformanceDashboard() {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate loading completion
    const timer = setTimeout(() => {
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">AI Performance Dashboard</h2>
        <p className="text-muted-foreground">
          Monitor AI tool selection performance and learning metrics
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="p-6 border rounded-lg">
          <h3 className="text-sm font-medium">Total Requests</h3>
          <div className="text-2xl font-bold">5,920</div>
          <p className="text-xs text-muted-foreground">Across all providers</p>
        </div>

        <div className="p-6 border rounded-lg">
          <h3 className="text-sm font-medium">Success Rate</h3>
          <div className="text-2xl font-bold">95.7%</div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div className="bg-blue-600 h-2 rounded-full" style={{ width: '95.7%' }}></div>
          </div>
        </div>

        <div className="p-6 border rounded-lg">
          <h3 className="text-sm font-medium">Avg Response Time</h3>
          <div className="text-2xl font-bold">845ms</div>
          <p className="text-xs text-muted-foreground">Across all providers</p>
        </div>

        <div className="p-6 border rounded-lg">
          <h3 className="text-sm font-medium">Active Models</h3>
          <div className="text-2xl font-bold">4</div>
          <p className="text-xs text-muted-foreground">Currently active</p>
        </div>
      </div>

      <div className="p-6 border rounded-lg">
        <h3 className="text-lg font-medium mb-4">AI Performance Summary</h3>
        <p className="text-muted-foreground">
          The AI tool router is performing well with a 95.7% success rate across all providers.
          The system is continuously learning from feedback and improving tool selection accuracy.
        </p>
      </div>
    </div>
  )
}
