export default function AppShellServer({ children }: { children: React.ReactNode }) {

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
      <main className="flex-1">
        {children}
      </main>
    </div>
  )
}
