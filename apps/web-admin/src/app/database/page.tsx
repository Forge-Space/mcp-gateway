'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Database,
  Table,
  Search,
  Plus,
  Download,
  Upload,
  RefreshCw,
  BarChart3,
  Users,
  Settings,
  Activity
} from 'lucide-react'

export default function DatabasePage() {
  const [tables, setTables] = useState([
    {
      name: 'users',
      rows: 1250,
      size: '2.4 MB',
      description: 'User authentication and profile data',
      lastModified: new Date('2026-02-18T10:30:00Z')
    },
    {
      name: 'virtual_servers',
      rows: 45,
      size: '156 KB',
      description: 'Virtual server configurations and status',
      lastModified: new Date('2026-02-18T14:15:00Z')
    },
    {
      name: 'server_templates',
      rows: 12,
      size: '89 KB',
      description: 'Reusable server templates',
      lastModified: new Date('2026-02-17T16:45:00Z')
    },
    {
      name: 'usage_analytics',
      rows: 15420,
      size: '18.7 MB',
      description: 'Usage metrics and activity logs',
      lastModified: new Date('2026-02-18T23:59:00Z')
    },
    {
      name: 'feature_toggles',
      rows: 17,
      size: '45 KB',
      description: 'Feature flag configurations',
      lastModified: new Date('2026-02-16T09:20:00Z')
    }
  ])

  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTable, setSelectedTable] = useState<string | null>(null)

  const filteredTables = tables.filter(table =>
    table.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    table.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const stats = [
    {
      title: 'Total Tables',
      value: tables.length,
      icon: Table,
      color: 'text-blue-600'
    },
    {
      title: 'Total Rows',
      value: tables.reduce((acc, table) => acc + table.rows, 0).toLocaleString(),
      icon: BarChart3,
      color: 'text-green-600'
    },
    {
      title: 'Database Size',
      value: '21.4 MB',
      icon: Database,
      color: 'text-purple-600'
    },
    {
      title: 'Active Connections',
      value: '8',
      icon: Activity,
      color: 'text-orange-600'
    }
  ]

  const formatBytes = (bytes: string) => bytes
  const formatDate = (date: Date) => date.toLocaleString()

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Database Management</h2>
          <p className="text-muted-foreground">
            Manage Supabase database tables, schema, and data operations
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button variant="outline">
            <Upload className="mr-2 h-4 w-4" />
            Import
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Table
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <Card key={index}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Search */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search tables..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <Database className="h-4 w-4" />
          <span>PostgreSQL via Supabase</span>
        </div>
      </div>

      {/* Tables List */}
      <div className="space-y-4">
        {filteredTables.map((table) => (
          <Card key={table.name} className="relative">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Table className="h-6 w-6 text-muted-foreground" />
                  <div>
                    <CardTitle className="text-lg font-mono">{table.name}</CardTitle>
                    <CardDescription>{table.description}</CardDescription>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">
                    {table.rows.toLocaleString()} rows
                  </Badge>
                  <Badge variant="outline">
                    {formatBytes(table.size)}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-medium mb-2">Table Statistics</h4>
                  <div className="space-y-1 text-sm text-muted-foreground">
                    <div>• Rows: {table.rows.toLocaleString()}</div>
                    <div>• Size: {formatBytes(table.size)}</div>
                    <div>• Last Modified: {formatDate(table.lastModified)}</div>
                    <div>• Type: PostgreSQL Table</div>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Quick Actions</h4>
                  <div className="space-y-1 text-sm text-muted-foreground">
                    <div>• View Data</div>
                    <div>• Edit Schema</div>
                    <div>• Export CSV</div>
                    <div>• Run Query</div>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                  <Activity className="h-4 w-4" />
                  <span>Active with RLS policies</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm">
                    <BarChart3 className="mr-2 h-4 w-4" />
                    Analytics
                  </Button>
                  <Button variant="outline" size="sm">
                    <Settings className="mr-2 h-4 w-4" />
                    Schema
                  </Button>
                  <Button variant="outline" size="sm">
                    <Table className="mr-2 h-4 w-4" />
                    View Data
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        {filteredTables.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <Database className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No tables found</h3>
              <p className="text-muted-foreground text-center mb-4">
                {searchTerm ? 'Try adjusting your search terms' : 'No database tables available'}
              </p>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Table
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Database Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="h-5 w-5" />
            <span>Database Configuration</span>
          </CardTitle>
          <CardDescription>
            Supabase PostgreSQL database settings and connection information
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-medium mb-2">Connection Details</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• Provider: Supabase</div>
                <div>• Database: PostgreSQL 15.1</div>
                <div>• Region: us-east-1</div>
                <div>• Pool Size: 20 connections</div>
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">Security Features</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• Row Level Security (RLS): Enabled</div>
                <div>• Encryption: At rest and in transit</div>
                <div>• Backups: Daily automated</div>
                <div>• Access Control: JWT-based</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Query Interface */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>SQL Query Interface</span>
          </CardTitle>
          <CardDescription>
            Execute custom SQL queries against the database
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="border rounded-lg p-4">
              <div className="font-mono text-sm text-muted-foreground mb-2">SQL Query Editor</div>
              <div className="bg-muted p-3 rounded text-sm font-mono">
                SELECT * FROM users WHERE created_at &gt; &apos;2026-02-01&apos;;
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline">
                <Table className="mr-2 h-4 w-4" />
                Execute Query
              </Button>
              <Button variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Export Results
              </Button>
              <Button variant="outline">
                <RefreshCw className="mr-2 h-4 w-4" />
                Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
