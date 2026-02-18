'use client'

import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { useAuthStore } from '@/lib/store'
import { Users, Plus, Edit, Trash2, Shield, UserCheck, UserX, Search } from 'lucide-react'

export function UserManagement() {
  const { users, loading, fetchUsers, user: currentUser } = useAuthStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [showCreateForm, setShowCreateForm] = useState(false)

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = roleFilter === 'all' || user.role === roleFilter
    const matchesStatus = statusFilter === 'all' ||
                         (statusFilter === 'active' && user.active) ||
                         (statusFilter === 'inactive' && !user.active)

    return matchesSearch && matchesRole && matchesStatus
  })

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin':
        return <Shield className="h-4 w-4" />
      case 'moderator':
        return <UserCheck className="h-4 w-4" />
      default:
        return <Users className="h-4 w-4" />
    }
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800'
      case 'moderator':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (active: boolean) => {
    return active ? UserCheck : UserX
  }

  const getStatusColor = (active: boolean) => {
    return active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleDateString()
  }

  const formatTime = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleTimeString()
  }

  const handleToggleUserStatus = async (userId: string, currentStatus: boolean) => {
    // In a real implementation, this would call the Supabase API
    console.log(`Toggle user ${userId} status to ${!currentStatus}`)
    // await toggleUserStatus(userId, !currentStatus)
    // await fetchUsers()
  }

  const handleDeleteUser = async (userId: string) => {
    if (confirm('Are you sure you want to delete this user?')) {
      // In a real implementation, this would call the Supabase API
      console.log(`Delete user ${userId}`)
      // await deleteUser(userId)
      // await fetchUsers()
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              User Management
            </CardTitle>
            <CardDescription>
              Manage users, roles, and permissions
            </CardDescription>
          </div>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add User
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="role-filter" className="text-sm font-medium text-gray-700">
              Role
            </Label>
            <Select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              <option value="all">All Roles</option>
              <option value="admin">Admin</option>
              <option value="moderator">Moderator</option>
              <option value="user">User</option>
            </Select>
          </div>
          <div>
            <Label htmlFor="status-filter" className="text-sm font-medium text-gray-700">
              Status
            </Label>
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </Select>
          </div>
        </div>

        {/* User Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold">{users.length}</div>
            <div className="text-sm text-gray-500">Total Users</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {users.filter(u => u.active).length}
            </div>
            <div className="text-sm text-gray-500">Active</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {users.filter(u => !u.active).length}
            </div>
            <div className="text-sm text-gray-500">Inactive</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {users.filter(u => u.role === 'admin').length}
            </div>
            <div className="text-sm text-gray-500">Admins</div>
          </div>
        </div>

        {/* User List */}
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-gray-500">Loading users...</div>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <Users className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500">No users found</p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredUsers.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-full bg-gray-100">
                      {getRoleIcon(user.role)}
                    </div>
                    <div>
                      <div className="font-medium">{user.name || 'Unknown'}</div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                      <div className="flex items-center space-x-2 mt-1">
                        <Badge className={getRoleColor(user.role)}>
                          {user.role}
                        </Badge>
                        <Badge className={getStatusColor(user.active)}>
                          {user.active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <div className="text-sm text-gray-500">Last Login</div>
                    <div className="text-sm">{formatDate(user.last_login)}</div>
                    <div className="text-xs text-gray-400">{formatTime(user.last_login)}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-500">Last Active</div>
                    <div className="text-sm">{formatDate(user.last_active)}</div>
                    <div className="text-xs text-gray-400">{formatTime(user.last_active)}</div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggleUserStatus(user.id, user.active)}
                      disabled={user.id === currentUser?.id}
                    >
                      {user.active ? (
                        <UserX className="h-4 w-4" />
                      ) : (
                        <UserCheck className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteUser(user.id)}
                      disabled={user.id === currentUser?.id}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
