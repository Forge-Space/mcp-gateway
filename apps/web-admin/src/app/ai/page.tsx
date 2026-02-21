'use client'

import AIPerformanceDashboard from '@/components/ai/ai-performance-dashboard-simple'

export const dynamic = 'force-dynamic'

export default function AIDashboard() {
  return (
    <div className="container mx-auto py-8">
      <AIPerformanceDashboard />
    </div>
  )
}
