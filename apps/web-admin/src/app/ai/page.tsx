'use client';

import { useState, useEffect } from 'react';
import AIPerformanceDashboard from '@/components/ai/ai-performance-dashboard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Trophy, FlaskConical, BarChart2, Users } from 'lucide-react';

export const dynamic = 'force-dynamic';

interface VariantStats {
  count: number;
  avg_score: number;
  avg_latency_ms: number;
  success_rate: number;
  min_score: number;
  max_score: number;
}

interface VariantSummary {
  name: string;
  weight: number;
  config: Record<string, unknown>;
}

interface ExperimentSummary {
  id: string;
  description: string;
  active: boolean;
  variant_count: number;
  variants: VariantSummary[];
  stats: Record<string, VariantStats>;
  winner: string | null;
}

interface ExperimentsResponse {
  experiments: ExperimentSummary[];
  total: number;
}

function ExperimentsSection() {
  const [data, setData] = useState<ExperimentsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExperiments = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/ai/experiments');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setData(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch experiments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperiments();
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-6 w-48 animate-pulse rounded bg-muted" />
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
        Failed to load experiments: {error}
        <button onClick={fetchExperiments} className="ml-4 underline">
          Retry
        </button>
      </div>
    );
  }

  const experiments = data?.experiments ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FlaskConical className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold">A/B Experiments</h2>
          <Badge variant="secondary">{data?.total ?? 0} total</Badge>
        </div>
        <button
          onClick={fetchExperiments}
          className="text-sm text-muted-foreground underline hover:text-foreground"
        >
          Refresh
        </button>
      </div>

      {experiments.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No A/B experiments registered. Experiments are created programmatically via
            ABTestManager.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {experiments.map((exp) => (
            <Card key={exp.id}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <CardTitle className="text-base">{exp.id}</CardTitle>
                    {exp.description && (
                      <CardDescription className="mt-0.5">{exp.description}</CardDescription>
                    )}
                  </div>
                  <Badge variant={exp.active ? 'default' : 'secondary'}>
                    {exp.active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Users className="h-3.5 w-3.5" />
                    {exp.variant_count} variants
                  </span>
                  {exp.winner && (
                    <span className="flex items-center gap-1 font-medium text-yellow-600">
                      <Trophy className="h-3.5 w-3.5" />
                      Winner: {exp.winner}
                    </span>
                  )}
                </div>

                {exp.variants.length > 0 && (
                  <div className="space-y-2">
                    {exp.variants.map((variant) => {
                      const stats = exp.stats[variant.name];
                      const isWinner = exp.winner === variant.name;
                      return (
                        <div
                          key={variant.name}
                          className={`rounded border p-2 text-sm ${isWinner ? 'border-yellow-500/50 bg-yellow-500/5' : 'border-border'}`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-medium">
                              {variant.name}
                              {isWinner && (
                                <Trophy className="ml-1 inline h-3.5 w-3.5 text-yellow-500" />
                              )}
                            </span>
                            <span className="text-muted-foreground">
                              weight: {variant.weight.toFixed(1)}
                            </span>
                          </div>
                          {stats ? (
                            <div className="mt-1 grid grid-cols-3 gap-1 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <BarChart2 className="h-3 w-3" />
                                {stats.count} samples
                              </span>
                              <span>score: {stats.avg_score.toFixed(2)}</span>
                              <span>success: {(stats.success_rate * 100).toFixed(0)}%</span>
                            </div>
                          ) : (
                            <div className="mt-1 text-xs text-muted-foreground">No data yet</div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default function AIDashboard() {
  return (
    <div className="container mx-auto space-y-8 py-8">
      <AIPerformanceDashboard />
      <ExperimentsSection />
    </div>
  );
}
