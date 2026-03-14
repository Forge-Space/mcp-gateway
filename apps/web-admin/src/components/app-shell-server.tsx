import { getSupabaseConfigError } from '@/lib/supabase-config'

export default function AppShellServer({ children }: { children: React.ReactNode }) {
  const configError = getSupabaseConfigError()

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="flex h-16 items-center px-4">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold">Forge MCP Gateway Admin</h1>
          </div>
          <div className="ml-auto">
            {/* Navigation will be rendered client-side via a separate mechanism */}
          </div>
        </div>
      </header>
      {configError ? (
        <div className="border-b border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          <strong className="font-semibold">Configuration required.</strong>{' '}
          {configError}
        </div>
      ) : null}
      <main className="flex-1">
        {children}
      </main>
    </div>
  )
}
