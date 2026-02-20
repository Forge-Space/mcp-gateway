'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Users, Plus, Search, Shield, Mail, Calendar, Activity } from 'lucide-react'
import AdvancedUserManagement from '@/components/users/advanced-user-management'

export default function UsersPage() {
  // Mock data for demonstration
  const mockUsers = [
    {
      id: '1',
      name: 'John Doe',
      email: 'john.doe@example.com',
      role: 'admin',
      created_at: new Date('2024-01-15'),
      last_login: new Date('2024-02-19'),
      status: 'active'
    },
    {
      id: '2',
      name: 'Jane Smith',
      email: 'jane.smith@example.com',
      role: 'user',
      created_at: new Date('2024-01-20'),
      last_login: new Date('2024-02-18'),
      status: 'active'
    },
    {
      id: '3',
      name: 'Bob Johnson',
      email: 'bob.johnson@example.com',
      role: 'moderator',
      created_at: new Date('2024-02-01'),
      last_login: new Date('2024-02-17'),
      status: 'inactive'
    }
  ]

  const [users] = useState(mockUsers)
  const [searchTerm, setSearchTerm] = useState('')
  const [loading] = useState(false)

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-500'
      case 'moderator':
        return 'bg-yellow-500'
      case 'user':
        return 'bg-green-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin':
        return <Shield className="h-3 w-3" />
      case 'moderator':
        return <Activity className="h-3 w-3" />
      case 'user':
        return <Users className="h-3 w-3" />
      default:
        return <Users className="h-3 w-3" />
    }
  }

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="container mx-auto py-8">
      <AdvancedUserManagement />

      {/* Users List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Users</h2>
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-64"
              />
            </div>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add User
            </Button>
          </div>
        </div>

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
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span>Joined: {user.created_at.toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Activity className="h-4 w-4 text-muted-foreground" />
                    <span>Last login: {user.last_login.toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${user.status === 'active' ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                    <span className="capitalize">{user.status}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Features Overview */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>User Management Features</CardTitle>
          <CardDescription>
            Comprehensive user authentication and authorization system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
