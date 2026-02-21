'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Server,
  Settings,
  BarChart3,
  Users,
  Zap,
  Hammer,
  Monitor,
  Brain,
  Globe,
  Shield,
  Database,
  Cpu,
  HardDrive,
  Network,
  Activity
} from 'lucide-react'

const navigation = [
  {
    name: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
    current: false
  },
  {
    name: 'AI Performance',
    href: '/ai',
    icon: Brain,
    current: false
  },
  {
    name: 'Monitoring',
    href: '/monitoring',
    icon: Activity,
    current: false
  },
  {
    name: 'Virtual Servers',
    href: '/servers',
    icon: Server,
    current: false
  },
  {
    name: 'IDE Integration',
    href: '/ide-integration',
    icon: Monitor,
    current: false
  },
  {
    name: 'MCP Builder',
    href: '/builder',
    icon: Hammer,
    current: false
  },
  {
    name: 'Feature Toggles',
    href: '/features',
    icon: Zap,
    current: false
  },
  {
    name: 'Templates',
    href: '/templates',
    icon: Settings,
    current: false
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
    current: false
  },
  {
    name: 'Users',
    href: '/users',
    icon: Users,
    current: false
  },
]

export default function Navigation() {
  const [pathname, setPathname] = useState('')

  useEffect(() => {
    // Use requestAnimationFrame to avoid setState in effect
    const updatePathname = () => {
      setPathname(window.location.pathname)
    }
    const animationId = requestAnimationFrame(updatePathname)
    return () => cancelAnimationFrame(animationId)
  }, [])

  return (
    <nav className="flex space-x-4 lg:space-x-6">
      {navigation.map((item) => {
        const isActive = pathname === item.href
        return (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              'flex items-center space-x-2 text-sm font-medium transition-colors hover:text-primary',
              isActive
                ? 'text-primary'
                : 'text-muted-foreground'
            )}
          >
            <item.icon className="h-4 w-4" />
            <span>{item.name}</span>
          </Link>
        )
      })}
    </nav>
  )
}
