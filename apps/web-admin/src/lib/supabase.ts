import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export type Database = {
  public: {
    Tables: {
      users: {
        Row: {
          id: string;
          email: string;
          name: string | null;
          role: 'admin' | 'moderator' | 'user';
          active: boolean;
          last_active: string | null;
          last_login: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          email: string;
          name?: string | null;
          role?: 'admin' | 'moderator' | 'user';
          active?: boolean;
          last_active?: string | null;
          last_login?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string;
          name?: string | null;
          role?: 'admin' | 'moderator' | 'user';
          active?: boolean;
          last_active?: string | null;
          last_login?: string | null;
          updated_at?: string;
        };
      };
      virtual_servers: {
        Row: {
          id: string;
          name: string;
          description: string;
          tools: string[];
          enabled: boolean;
          port: number | null;
          host: string | null;
          created_by: string;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          name: string;
          description: string;
          tools: string[];
          enabled?: boolean;
          port?: number | null;
          host?: string | null;
          created_by: string;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          name?: string;
          description?: string;
          tools?: string[];
          enabled?: boolean;
          port?: number | null;
          host?: string | null;
          updated_at?: string;
        };
      };
      server_templates: {
        Row: {
          id: string;
          name: string;
          description: string;
          category: string;
          tools: string[];
          config: Record<string, unknown>;
          version: string | null;
          deployments: number;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          name: string;
          description: string;
          category: string;
          tools: string[];
          config: Record<string, unknown>;
          version?: string | null;
          deployments?: number;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          name?: string;
          description?: string;
          category?: string;
          tools?: string[];
          config?: Record<string, unknown>;
          version?: string | null;
          deployments?: number;
          updated_at?: string;
        };
      };
      usage_analytics: {
        Row: {
          id: string;
          server_id: string;
          user_id: string;
          action: string;
          metadata: Record<string, unknown>;
          timestamp: string;
        };
        Insert: {
          id?: string;
          server_id: string;
          user_id: string;
          action: string;
          metadata: Record<string, unknown>;
          timestamp?: string;
        };
        Update: {
          id?: string;
          server_id?: string;
          user_id?: string;
          action?: string;
          metadata?: Record<string, unknown>;
          timestamp?: string;
        };
      };
      mcp_server_definitions: {
        Row: {
          id: string;
          name: string;
          description: string | null;
          server_type: string;
          transport: string;
          port: number;
          docker_image: string | null;
          environment: Record<string, string>;
          config: Record<string, unknown>;
          status: 'pending' | 'running' | 'stopped' | 'error';
          created_by: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          name: string;
          description?: string | null;
          server_type: string;
          transport?: string;
          port: number;
          docker_image?: string | null;
          environment?: Record<string, string>;
          config?: Record<string, unknown>;
          status?: 'pending' | 'running' | 'stopped' | 'error';
          created_by?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          name?: string;
          description?: string | null;
          server_type?: string;
          transport?: string;
          port?: number;
          docker_image?: string | null;
          environment?: Record<string, string>;
          config?: Record<string, unknown>;
          status?: 'pending' | 'running' | 'stopped' | 'error';
          updated_at?: string;
        };
      };
    };
  };
};
