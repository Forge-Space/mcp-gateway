import { create } from 'zustand'

import { supabase, type Database } from './supabase'

type User = Database['public']['Tables']['users']['Row']
type VirtualServer = Database['public']['Tables']['virtual_servers']['Row']
type ServerTemplate = Database['public']['Tables']['server_templates']['Row']
type UsageAnalytics = Database['public']['Tables']['usage_analytics']['Row']

interface AuthState {
  user: User | null
  users: User[]
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  refreshUser: () => Promise<void>
  fetchUsers: () => Promise<void>
}

interface ServerState {
  servers: VirtualServer[]
  templates: ServerTemplate[]
  loading: boolean
  fetchServers: () => Promise<void>
  fetchTemplates: () => Promise<void>
  createServer: (server: Omit<VirtualServer, 'id' | 'created_at' | 'updated_at'>) => Promise<void>
  updateServer: (id: string, updates: Partial<VirtualServer>) => Promise<void>
  deleteServer: (id: string) => Promise<void>
  toggleServer: (id: string) => Promise<void>
}

interface AnalyticsState {
  analytics: UsageAnalytics[]
  loading: boolean
  fetchAnalytics: (serverId?: string, timeframe?: string) => Promise<void>
  trackUsage: (serverId: string, action: string, metadata?: Record<string, unknown>) => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  users: [],
  loading: false,
  fetchUsers: async () => {
    set({ loading: true })
    try {
      const { data } = await supabase
        .from('users')
        .select('*')
        .order('created_at', { ascending: false })
      set({ users: data || [] })
    } catch (error) {
      console.error('Fetch users error:', error)
    } finally {
      set({ loading: false })
    }
  },
  signIn: async (email: string, password: string) => {
    set({ loading: true })
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      if (error) {throw error}
      await get().refreshUser()
    } catch (error) {
      console.error('Sign in error:', error)
      throw error
    } finally {
      set({ loading: false })
    }
  },
  signOut: async () => {
    set({ loading: true })
    try {
      await supabase.auth.signOut()
      set({ user: null })
    } catch (error) {
      console.error('Sign out error:', error)
    } finally {
      set({ loading: false })
    }
  },
  refreshUser: async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (user) {
        const { data: userData } = await supabase
          .from('users')
          .select('*')
          .eq('id', user.id)
          .single()
        set({ user: userData })
      }
    } catch (error) {
      console.error('Refresh user error:', error)
    }
  },
}))

export const useServerStore = create<ServerState>((set, get) => ({
  servers: [],
  templates: [],
  loading: false,
  fetchServers: async () => {
    set({ loading: true })
    try {
      const { data } = await supabase
        .from('virtual_servers')
        .select('*')
        .order('created_at', { ascending: false })
      set({ servers: data || [] })
    } catch (error) {
      console.error('Fetch servers error:', error)
    } finally {
      set({ loading: false })
    }
  },
  fetchTemplates: async () => {
    set({ loading: true })
    try {
      const { data } = await supabase
        .from('server_templates')
        .select('*')
        .order('name', { ascending: true })
      set({ templates: data || [] })
    } catch (error) {
      console.error('Fetch templates error:', error)
    } finally {
      set({ loading: false })
    }
  },
  createServer: async (server) => {
    try {
      const { data } = await supabase
        .from('virtual_servers')
        .insert(server)
        .select()
        .single()
      if (data) {
        set(state => ({ servers: [data, ...state.servers] }))
      }
    } catch (error) {
      console.error('Create server error:', error)
      throw error
    }
  },
  updateServer: async (id, updates) => {
    try {
      const { data } = await supabase
        .from('virtual_servers')
        .update(updates)
        .eq('id', id)
        .select()
        .single()
      if (data) {
        set(state => ({
          servers: state.servers.map(server =>
            server.id === id ? data : server
          )
        }))
      }
    } catch (error) {
      console.error('Update server error:', error)
      throw error
    }
  },
  deleteServer: async (id) => {
    try {
      await supabase.from('virtual_servers').delete().eq('id', id)
      set(state => ({
        servers: state.servers.filter(server => server.id !== id)
      }))
    } catch (error) {
      console.error('Delete server error:', error)
      throw error
    }
  },
  toggleServer: async (id) => {
    const server = get().servers.find(s => s.id === id)
    if (server) {
      await get().updateServer(id, { enabled: !server.enabled })
    }
  },
}))

export const useAnalyticsStore = create<AnalyticsState>((set, get) => ({
  analytics: [],
  loading: false,
  fetchAnalytics: async (serverId?: string, timeframe?: string) => {
    set({ loading: true })
    try {
      let query = supabase.from('usage_analytics').select('*')

      if (serverId) {
        query = query.eq('server_id', serverId)
      }

      if (timeframe) {
        const now = new Date()
        let startDate: Date

        switch (timeframe) {
          case '24h':
            startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000)
            break
          case '7d':
            startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
            break
          case '30d':
            startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
            break
          default:
            startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000)
        }

        query = query.gte('timestamp', startDate.toISOString())
      }

      const { data } = await query.order('timestamp', { ascending: false })
      set({ analytics: data || [] })
    } catch (error) {
      console.error('Fetch analytics error:', error)
    } finally {
      set({ loading: false })
    }
  },
  trackUsage: async (serverId: string, action: string, metadata: Record<string, unknown> = {}) => {
    try {
      const { data: user } = await supabase.auth.getUser()
      if (!user.user) {return}

      await supabase.from('usage_analytics').insert({
        server_id: serverId,
        user_id: user.user.id,
        action,
        metadata,
        timestamp: new Date().toISOString(),
      })
    } catch (error) {
      console.error('Track usage error:', error)
    }
  },
}))
