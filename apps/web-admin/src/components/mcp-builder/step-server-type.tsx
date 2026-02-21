'use client'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { SERVER_TYPE_CATALOG, type ServerTypeId } from '@/lib/mcp-server-catalog'
import {
  Brain,
  Code,
  Database,
  FolderOpen,
  Github,
  Globe,
  Lightbulb,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface StepServerTypeProps {
  selected: ServerTypeId | null
  onSelect: (id: ServerTypeId) => void
}

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  FolderOpen,
  Github,
  Globe,
  Brain,
  Database,
  Lightbulb,
  Code,
}

const CATEGORY_LABELS: Record<string, string> = {
  tools: 'Tools',
  data: 'Data',
  ai: 'AI',
  custom: 'Custom',
}

const CATEGORY_COLORS: Record<string, string> = {
  tools: 'bg-blue-100 text-blue-800',
  data: 'bg-green-100 text-green-800',
  ai: 'bg-purple-100 text-purple-800',
  custom: 'bg-orange-100 text-orange-800',
}

const BADGE_COLORS: Record<string, string> = {
  Popular: 'bg-yellow-100 text-yellow-800',
  AI: 'bg-purple-100 text-purple-800',
  Advanced: 'bg-orange-100 text-orange-800',
}

export function StepServerType({ selected, onSelect }: StepServerTypeProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Choose a server type</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Select the type of MCP server you want to add to the Forge Gateway.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {SERVER_TYPE_CATALOG.map((serverType) => {
          const Icon = ICON_MAP[serverType.icon] ?? Code
          const isSelected = selected === serverType.id

          return (
            <Card
              key={serverType.id}
              className={cn(
                'cursor-pointer transition-all hover:shadow-md hover:border-primary/50',
                isSelected && 'border-primary ring-2 ring-primary/20 shadow-md'
              )}
              onClick={() => onSelect(serverType.id)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div
                    className={cn(
                      'p-2 rounded-lg',
                      isSelected ? 'bg-primary/10' : 'bg-muted'
                    )}
                  >
                    <Icon className={cn('h-5 w-5', isSelected ? 'text-primary' : 'text-muted-foreground')} />
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    {serverType.badge && (
                      <Badge className={cn('text-xs', BADGE_COLORS[serverType.badge] ?? 'bg-gray-100 text-gray-800')}>
                        {serverType.badge}
                      </Badge>
                    )}
                    <Badge
                      variant="outline"
                      className={cn('text-xs', CATEGORY_COLORS[serverType.category])}
                    >
                      {CATEGORY_LABELS[serverType.category]}
                    </Badge>
                  </div>
                </div>
                <CardTitle className="text-sm mt-2">{serverType.name}</CardTitle>
              </CardHeader>
              <CardContent className="pb-3">
                <CardDescription className="text-xs leading-relaxed">
                  {serverType.description}
                </CardDescription>
                <div className="mt-2 text-xs text-muted-foreground">
                  {serverType.defaultTools.length > 0
                    ? `${serverType.defaultTools.length} default tools`
                    : 'Custom tools'}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
