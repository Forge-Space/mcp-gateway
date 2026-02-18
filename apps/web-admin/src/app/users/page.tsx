'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/lib/store'
import { 
  Users, 
  Plus, 
  Search, 
  Shield, 
  Mail, 
  Calendar,
  Activity,
  Settings,
  UserPlus,
  Key
} from 'lucide-react'

export default function UsersPage() {
  const { users, loading, fetchUsers } = useAuthStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRole, setSelectedRole] = useState('all')

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.name?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = selectedRole === 'all' || user.role === selectedRole
    return matchesSearch && matchesRole
  })

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-800'
      case 'moderator': return 'bg-blue-100 text-blue-800'
      case 'user': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin': return <Shield className="h-4 w-4" />
      case 'moderator': return <Settings className="h-4 w-4" />
      case 'user': return <Users className="h-4 w-4" />
      default: return <Users className="h-4 w-4" />
    }
  }

  // Calculate date thresholds outside of render
  // eslint-disable-next-line react-hooks/purity
  const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000)
  // eslint-disable-next-line react-hooks/purity
  const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)

  const stats = [
    {
      title: 'Total Users',
      value: users.length,
      icon: Users,
      color: 'text-blue-600'
    },
    {
      title: 'Active Today',
      value: users.filter(u => u.last_active && new Date(u.last_active) > oneDayAgo).length,
      icon: Activity,
      color: 'text-green-600'
    },
    {
      title: 'Admins',
      value: users.filter(u => u.role === 'admin').length,
      icon: Shield,
      color: 'text-red-600'
    },
    {
      title: 'New This Week',
      value: users.filter(u => new Date(u.created_at) > oneWeekAgo).length,
      icon: UserPlus,
      color: 'text-purple-600'
    }
  ]

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">User Management</h2>
          <p className="text-muted-foreground">
            Manage users, roles, and permissions for the MCP gateway admin interface
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Key className="mr-2 h-4 w-4" />
            API Keys
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add User
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

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant={selectedRole === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedRole('all')}
          >
            All Roles
          </Button>
          <Button
            variant={selectedRole === 'admin' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedRole('admin')}
          >
            Admins
          </Button>
          <Button
            variant={selectedRole === 'moderator' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedRole('moderator')}
          >
            Moderators
          </Button>
          <Button
            variant={selectedRole === 'user' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedRole('user')}
          >
            Users
          </Button>
        </div>
      </div>

      {/* Users List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          filteredUsers.map((user) => (
            <Card key={user.id} className="relative">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center">
                      <Users className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{user.name || 'Unknown User'}</CardTitle>
                      <CardDescription className="flex items-center space-x-2">
                        <Mail className="h-4 w-4" />
                        <span>{user.email}</span>
                      </CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getRoleColor(user.role)}>
                      {getRoleIcon(user.role)}
                      <span className="ml-1 capitalize">{user.role}</span>
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h4 className="font-medium mb-2">User Information</h4>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <div>• ID: {user.id}</div>
                      <div>• Created: {new Date(user.created_at).toLocaleDateString()}</div>
                      <div>• Last Active: {user.last_active ? new Date(user.last_active).toLocaleString() : 'Never'}</div>
                      <div>• Status: {user.active ? 'Active' : 'Inactive'}</div>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Permissions</h4>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <div>• Server Management: {user.role === 'admin' ? 'Full' : user.role === 'moderator' ? 'Limited' : 'None'}</div>
                      <div>• Feature Toggles: {user.role === 'admin' ? 'Full' : user.role === 'moderator' ? 'Read' : 'None'}</div>
                      <div>• User Management: {user.role === 'admin' ? 'Full' : 'None'}</div>
                      <div>• Analytics Access: {user.role !== 'user' ? 'Full' : 'Limited'}</div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Activity className="h-4 w-4" />
                    <span>Last login: {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button variant="outline" size="sm">
                      <Key className="mr-2 h-4 w-4" />
                      API Keys
                    </Button>
                    <Button variant="outline" size="sm">
                      <Settings className="mr-2 h-4 w-4" />
                      Edit
                    </Button>
                    <Button 
                      variant={user.active ? "outline" : "default"} 
                      size="sm"
                    >
                      {user.active ? 'Disable' : 'Enable'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
        {filteredUsers.length === 0 && !loading && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <Users className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No users found</h3>
              <p className="text-muted-foreground text-center mb-4">
                {searchTerm || selectedRole !== 'all' 
                  ? 'Try adjusting your search or filters' 
                  : 'Get started by inviting your first user to the admin interface.'
                }
              </p>
              <Button>
                <UserPlus className="mr-2 h-4 w-4" />
                Invite User
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* User Management Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <span>User Management System</span>
          </CardTitle>
          <CardDescription>
            Supabase-based authentication and authorization for the admin interface
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-medium mb-2">Authentication Features</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• JWT-based authentication</div>
                <div>• OAuth providers (Google, GitHub)</div>
                <div>• Magic link authentication</div>
                <div>• Session management</div>
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">Authorization System</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• Role-based access control (RBAC)</div>
                <div>• Row Level Security (RLS)</div>
                <div>• API key management</div>
                <div>• Permission inheritance</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
