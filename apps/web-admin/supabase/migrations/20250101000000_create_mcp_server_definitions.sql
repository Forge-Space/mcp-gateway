-- Migration: Create mcp_server_definitions table
-- This table stores MCP server configurations created via the MCP Builder UI.

CREATE TABLE IF NOT EXISTS public.mcp_server_definitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  server_type TEXT NOT NULL,
  transport TEXT NOT NULL DEFAULT 'SSE',
  port INTEGER NOT NULL,
  docker_image TEXT,
  environment JSONB NOT NULL DEFAULT '{}',
  config JSONB NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'running', 'stopped', 'error')),
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.mcp_server_definitions ENABLE ROW LEVEL SECURITY;

-- Users can only see and manage their own server definitions
CREATE POLICY "Users can manage their own server definitions"
  ON public.mcp_server_definitions
  FOR ALL
  USING (auth.uid() = created_by);

-- Admins can see all server definitions (requires a role check via users table)
CREATE POLICY "Admins can view all server definitions"
  ON public.mcp_server_definitions
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.users
      WHERE id = auth.uid()::text
        AND role = 'admin'
    )
  );

-- Auto-update updated_at on row modification
CREATE OR REPLACE FUNCTION public.update_mcp_server_definitions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mcp_server_definitions_updated_at
  BEFORE UPDATE ON public.mcp_server_definitions
  FOR EACH ROW
  EXECUTE FUNCTION public.update_mcp_server_definitions_updated_at();
