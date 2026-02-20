'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
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
  Key,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  Download,
  Upload,
  Filter,
  Bell,
  BellOff,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Zap,
  Database,
  Globe,
  Cpu,
  HardDrive,
  Network,
  RefreshCw,
  Save,
  X,
  MoreHorizontal,
  UserCheck,
  UserX,
  Lock,
  Unlock,
  ShieldCheck,
  ShieldAlert,
  UserCog,
  Users2,
  Crown,
  Star,
  Award,
  Target,
  TrendingUp,
  BarChart3,
  PieChart,
  ActivitySquare
} from 'lucide-react'

interface Permission {
  id: string
  name: string
  description: string
  category: 'servers' | 'users' | 'monitoring' | 'settings' | 'analytics'
  granted: boolean
}

interface Role {
  id: string
  name: string
  description: string
  level: number
  permissions: string[]
  userCount: number
  isActive: boolean
}

interface UserActivity {
  id: string
  userId: string
  action: string
  resource: string
  timestamp: string
  ipAddress: string
  userAgent: string
  success: boolean
}

interface UserSession {
  id: string
  userId: string
  startedAt: string
  lastActivity: string
  ipAddress: string
  userAgent: string
  isActive: boolean
  duration: string
}

export default function AdvancedUserManagement() {
  const { users, loading, fetchUsers } = useAuthStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRole, setSelectedRole] = useState('all')
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [showRoleManagement, setShowRoleManagement] = useState(false)
  const [showUserDetails, setShowUserDetails] = useState(false)
  const [selectedUser, setSelectedUser] = useState<{ id: string; name: string | null; email: string; role: "admin" | "moderator" | "user" } | null>(null)
  const [activeTab, setActiveTab] = useState<'users' | 'roles' | 'permissions' | 'activity' | 'sessions'>('users')
  const [showBulkActions, setShowBulkActions] = useState(false)
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])

  // Mock data for roles and permissions
  const [roles] = useState<Role[]>([
    {
      id: '1',
      name: 'Super Admin',
      description: 'Full system access with all permissions',
      level: 100,
      permissions: ['*'],
      userCount: 1,
      isActive: true
    },
    {
      id: '2',
      name: 'Admin',
      description: 'Administrative access to most features',
      level: 80,
      permissions: ['servers.*', 'users.read', 'users.write', 'monitoring.*', 'settings.read'],
      userCount: 3,
      isActive: true
    },
    {
      id: '3',
      name: 'Moderator',
      description: 'Can manage users and view monitoring',
      level: 60,
      permissions: ['users.read', 'users.write', 'monitoring.read', 'analytics.read'],
      userCount: 5,
      isActive: true
    },
    {
      id: '4',
      name: 'Developer',
      description: 'Can manage servers and view analytics',
      level: 40,
      permissions: ['servers.*', 'analytics.read', 'monitoring.read'],
      userCount: 12,
      isActive: true
    },
    {
      id: '5',
      name: 'Viewer',
      description: 'Read-only access to monitoring and analytics',
      level: 20,
      permissions: ['monitoring.read', 'analytics.read'],
      userCount: 25,
      isActive: true
    }
  ])

  const [permissions] = useState<Permission[]>([
    // Server permissions
    { id: 'servers.read', name: 'View Servers', description: 'View server list and details', category: 'servers', granted: false },
    { id: 'servers.write', name: 'Manage Servers', description: 'Create, edit, and delete servers', category: 'servers', granted: false },
    { id: 'servers.deploy', name: 'Deploy Servers', description: 'Deploy servers to production', category: 'servers', granted: false },
    { id: 'servers.control', name: 'Control Servers', description: 'Start, stop, restart servers', category: 'servers', granted: false },

    // User permissions
    { id: 'users.read', name: 'View Users', description: 'View user list and profiles', category: 'users', granted: false },
    { id: 'users.write', name: 'Manage Users', description: 'Create, edit, and delete users', category: 'users', granted: false },
    { id: 'users.roles', name: 'Manage Roles', description: 'Assign and manage user roles', category: 'users', granted: false },
    { id: 'users.permissions', name: 'Manage Permissions', description: 'Grant and revoke permissions', category: 'users', granted: false },

    // Monitoring permissions
    { id: 'monitoring.read', name: 'View Monitoring', description: 'View system monitoring data', category: 'monitoring', granted: false },
    { id: 'monitoring.alerts', name: 'Manage Alerts', description: 'Configure and manage alerts', category: 'monitoring', granted: false },
    { id: 'monitoring.logs', name: 'View Logs', description: 'Access system and service logs', category: 'monitoring', granted: false },

    // Settings permissions
    { id: 'settings.read', name: 'View Settings', description: 'View system configuration', category: 'settings', granted: false },
    { id: 'settings.write', name: 'Manage Settings', description: 'Modify system configuration', category: 'settings', granted: false },

    // Analytics permissions
    { id: 'analytics.read', name: 'View Analytics', description: 'View usage analytics and reports', category: 'analytics', granted: false },
    { id: 'analytics.export', name: 'Export Analytics', description: 'Export analytics data', category: 'analytics', granted: false }
  ])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.name?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = selectedRole === 'all' || user.role === selectedRole
    const matchesStatus = selectedStatus === 'all' ||
                        (selectedStatus === 'active' && user.last_login) ||
                        (selectedStatus === 'inactive' && !user.last_login)
    return matchesSearch && matchesRole && matchesStatus
  })

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-800 border-red-200'
      case 'moderator': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'developer': return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'user': return 'bg-green-100 text-green-800 border-green-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin': return <Crown className="h-4 w-4" />
      case 'moderator': return <ShieldCheck className="h-4 w-4" />
      case 'developer': return <UserCog className="h-4 w-4" />
      case 'user': return <Users className="h-4 w-4" />
      default: return <Users className="h-4 w-4" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      case 'suspended': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getPermissionIcon = (category: string) => {
    switch (category) {
      case 'servers': return <Database className="h-4 w-4" />
      case 'users': return <Users2 className="h-4 w-4" />
      case 'monitoring': return <ActivitySquare className="h-4 w-4" />
      case 'settings': return <Settings className="h-4 w-4" />
      case 'analytics': return <BarChart3 className="h-4 w-4" />
      default: return <Key className="h-4 w-4" />
    }
  }

  const handleUserSelection = (userId: string) => {
    setSelectedUsers(prev =>
      prev.includes(userId)
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    )
  }

  const handleBulkAction = (action: string) => {
    console.log(`Bulk action: ${action} on users:`, selectedUsers)
    // Implement bulk actions here
  }

  const renderUsersTab = () => (
    <div className="space-y-6">
      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              User Management ({filteredUsers.length})
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowBulkActions(!showBulkActions)}
                className="flex items-center gap-2"
              >
                <Filter className="h-4 w-4" />
                Bulk Actions
              </Button>
              <Button
                onClick={() => setShowCreateUser(true)}
                className="flex items-center gap-2"
              >
                <UserPlus className="h-4 w-4" />
                Add User
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search users by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="w-40 px-3 py-2 border rounded-md bg-background"
            >
              <option value="all">All Roles</option>
              {roles.map(role => (
                <option key={role.id} value={role.name.toLowerCase()}>
                  {role.name}
                </option>
              ))}
            </select>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-32 px-3 py-2 border rounded-md bg-background"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="suspended">Suspended</option>
            </select>
          </div>

          {/* Bulk Actions */}
          {showBulkActions && selectedUsers.length > 0 && (
            <div className="mb-4 p-4 bg-muted rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  {selectedUsers.length} users selected
                </span>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleBulkAction('activate')}>
                    <UserCheck className="h-4 w-4 mr-1" />
                    Activate
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => handleBulkAction('deactivate')}>
                    <UserX className="h-4 w-4 mr-1" />
                    Deactivate
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => handleBulkAction('role')}>
                    <Shield className="h-4 w-4 mr-1" />
                    Change Role
                  </Button>
                  <Button variant="destructive" size="sm" onClick={() => handleBulkAction('delete')}>
                    <Trash2 className="h-4 w-4 mr-1" />
                    Delete
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Users Table */}
          <div className="rounded-md border">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="p-4 text-left font-medium">
                      <input
                        type="checkbox"
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedUsers(filteredUsers.map(u => u.id))
                          } else {
                            setSelectedUsers([])
                          }
                        }}
                        className="rounded"
                      />
                    </th>
                    <th className="p-4 text-left font-medium">User</th>
                    <th className="p-4 text-left font-medium">Role</th>
                    <th className="p-4 text-left font-medium">Status</th>
                    <th className="p-4 text-left font-medium">Last Active</th>
                    <th className="p-4 text-left font-medium">Created</th>
                    <th className="p-4 text-left font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="border-b hover:bg-muted/50">
                      <td className="p-4">
                        <input
                          type="checkbox"
                          checked={selectedUsers.includes(user.id)}
                          onChange={() => handleUserSelection(user.id)}
                          className="rounded"
                        />
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                            <span className="text-sm font-medium">
                              {user.email?.charAt(0).toUpperCase()}
                            </span>
                          </div>
                          <div>
                            <div className="font-medium">{user.name || 'Unknown'}</div>
                            <div className="text-sm text-muted-foreground">{user.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <Badge className={`flex items-center gap-1 ${getRoleColor(user.role)}`}>
                          {getRoleIcon(user.role)}
                          {user.role || 'user'}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <Badge className={getStatusColor('active')}>
                          {user.last_login ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                      <td className="p-4 text-sm text-muted-foreground">
                        {user.last_login
                          ? new Date(user.last_login).toLocaleDateString()
                          : 'Never'
                        }
                      </td>
                      <td className="p-4 text-sm text-muted-foreground">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedUser(user)
                              setShowUserDetails(true)
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedUser(user)
                              setShowCreateUser(true)
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive hover:text-destructive"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderRolesTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Role Management
            </span>
            <Button onClick={() => setShowRoleManagement(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Role
            </Button>
          </CardTitle>
          <CardDescription>
            Define and manage user roles with specific permissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {roles.map((role) => (
              <Card key={role.id} className="relative">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        role.level >= 80 ? 'bg-red-100' :
                        role.level >= 60 ? 'bg-blue-100' :
                        role.level >= 40 ? 'bg-purple-100' :
                        'bg-green-100'
                      }`}>
                        {getRoleIcon(role.name.toLowerCase())}
                      </div>
                      <div>
                        <CardTitle className="text-sm">{role.name}</CardTitle>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>Level {role.level}</span>
                          <span>•</span>
                          <span>{role.userCount} users</span>
                        </div>
                      </div>
                    </div>
                    <Switch checked={role.isActive} />
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm text-muted-foreground mb-3">
                    {role.description}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {role.permissions.slice(0, 3).map((permission, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {permission}
                      </Badge>
                    ))}
                    {role.permissions.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{role.permissions.length - 3} more
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-3">
                    <Button variant="ghost" size="sm" className="h-8">
                      <Edit className="h-3 w-3 mr-1" />
                      Edit
                    </Button>
                    <Button variant="ghost" size="sm" className="h-8">
                      <Users className="h-3 w-3 mr-1" />
                      View Users
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderPermissionsTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Permission Management
          </CardTitle>
          <CardDescription>
            Configure granular permissions for different system resources
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {['servers', 'users', 'monitoring', 'settings', 'analytics'].map((category) => (
              <div key={category}>
                <div className="flex items-center gap-2 mb-3">
                  {getPermissionIcon(category)}
                  <h3 className="text-lg font-semibold capitalize">{category} Permissions</h3>
                </div>
                <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {permissions
                    .filter(p => p.category === category)
                    .map((permission) => (
                      <Card key={permission.id} className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Switch checked={permission.granted} />
                            <span className="font-medium">{permission.name}</span>
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {permission.category}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {permission.description}
                        </p>
                      </Card>
                    ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderActivityTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            User Activity Log
          </CardTitle>
          <CardDescription>
            Monitor user actions and system events
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Mock activity data */}
            {[
              { user: 'admin@example.com', action: 'Created server', resource: 'web-server-01', time: '2 minutes ago', success: true },
              { user: 'dev@example.com', action: 'Modified settings', resource: 'monitoring', time: '15 minutes ago', success: true },
              { user: 'user@example.com', action: 'Failed login', resource: 'auth', time: '1 hour ago', success: false },
              { user: 'mod@example.com', action: 'Updated user role', resource: 'users', time: '2 hours ago', success: true },
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.success ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <div>
                    <div className="font-medium">{activity.user}</div>
                    <div className="text-sm text-muted-foreground">
                      {activity.action} • {activity.resource}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm">{activity.time}</div>
                  <Badge variant={activity.success ? 'default' : 'destructive'} className="text-xs">
                    {activity.success ? 'Success' : 'Failed'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSessionsTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Active Sessions
          </CardTitle>
          <CardDescription>
            Monitor and manage user sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Mock session data */}
            {[
              { user: 'admin@example.com', ip: '192.168.1.100', duration: '2h 15m', lastActivity: 'Active now' },
              { user: 'dev@example.com', ip: '192.168.1.101', duration: '45m', lastActivity: '5 minutes ago' },
              { user: 'user@example.com', ip: '192.168.1.102', duration: '1h 30m', lastActivity: '12 minutes ago' },
            ].map((session, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <div>
                    <div className="font-medium">{session.user}</div>
                    <div className="text-sm text-muted-foreground">
                      IP: {session.ip} • Duration: {session.duration}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">{session.lastActivity}</span>
                  <Button variant="outline" size="sm">
                    <Eye className="h-4 w-4 mr-1" />
                    View
                  </Button>
                  <Button variant="outline" size="sm" className="text-destructive">
                    <XCircle className="h-4 w-4 mr-1" />
                    Terminate
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Advanced User Management</h1>
          <p className="text-muted-foreground">
            Comprehensive user, role, and permission management
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export Users
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Import Users
          </Button>
          <Button className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Users</p>
                <p className="text-2xl font-bold">{users.length}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
            <div className="mt-2 flex items-center text-sm text-muted-foreground">
              <TrendingUp className="h-4 w-4 mr-1 text-green-500" />
              +12% from last month
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Users</p>
                <p className="text-2xl font-bold">
                  {users.filter(u => u.last_login).length}
                </p>
              </div>
              <Activity className="h-8 w-8 text-green-500" />
            </div>
            <div className="mt-2 flex items-center text-sm text-muted-foreground">
              <TrendingUp className="h-4 w-4 mr-1 text-green-500" />
              +8% from last week
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Roles</p>
                <p className="text-2xl font-bold">{roles.length}</p>
              </div>
              <Shield className="h-8 w-8 text-purple-500" />
            </div>
            <div className="mt-2 flex items-center text-sm text-muted-foreground">
              <span className="text-blue-500">5 active roles</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Permissions</p>
                <p className="text-2xl font-bold">{permissions.length}</p>
              </div>
              <Key className="h-8 w-8 text-orange-500" />
            </div>
            <div className="mt-2 flex items-center text-sm text-muted-foreground">
              <span className="text-blue-500">14 permissions</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4 border-b">
            {[
              { id: 'users', label: 'Users', icon: Users },
              { id: 'roles', label: 'Roles', icon: Shield },
              { id: 'permissions', label: 'Permissions', icon: Key },
              { id: 'activity', label: 'Activity', icon: Activity },
              { id: 'sessions', label: 'Sessions', icon: Clock },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'users' | 'roles' | 'permissions' | 'activity' | 'sessions')}
                className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {activeTab === 'users' && renderUsersTab()}
          {activeTab === 'roles' && renderRolesTab()}
          {activeTab === 'permissions' && renderPermissionsTab()}
          {activeTab === 'activity' && renderActivityTab()}
          {activeTab === 'sessions' && renderSessionsTab()}
        </CardContent>
      </Card>
    </div>
  )
}
