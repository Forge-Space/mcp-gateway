'use client'

import { Suspense } from 'react'
import Navigation from './navigation'

export default function NavigationWrapper() {
  return (
    <Suspense fallback={null}>
      <Navigation />
    </Suspense>
  )
}
