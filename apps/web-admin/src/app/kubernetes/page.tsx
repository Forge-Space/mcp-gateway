'use client'

import KubernetesDeployment from '@/components/kubernetes/kubernetes-deployment'

export default function KubernetesPage() {
  return (
    <div className="container mx-auto py-8">
      <KubernetesDeployment />
    </div>
  )
}
