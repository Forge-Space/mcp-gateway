'use client';

import { useState, useEffect } from 'react';
import AIPerformanceDashboard from '@/components/ai/ai-performance-dashboard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Trophy,
  FlaskConical,
  BarChart2,
  Users,
  Brain,
  TrendingUp,
  AlertTriangle,
  Cpu,
} from 'lucide-react';

export const dynamic = 'force-dynamic';

// --- A/B Experiments types ---
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

// --- ML Metrics types ---
interface ToolStatsSummary {
  tool_name: string;
  success_count: number;
  failure_count: number;
  total: number;
  success_rate: number;
  avg_confidence: number;
  recent_success_rate: number;
  confidence_score: number;
  top_task_types: string[];
  top_intents: string[];
}

interface FeedbackStats {
  total_entries: number;
  total_tools: number;
  tool_stats: Record<string, ToolStatsSummary>;
}

interface ModelUsage {
  model: string;
  usage_count: number;
  total_tokens: number;
  total_cost: number;
}

interface SelectorMetrics {
  total_requests: number;
  total_cost_saved: number;
  avg_response_time_ms: number;
  model_usage: ModelUsage[];
  cost_optimization_enabled: boolean;
}

interface LearningHealth {
  top_performing_tools: string[];
  low_confidence_tools: string[];
  most_used_task_types: string[];
}

interface MLMetricsResponse {
  timestamp: string;
  feedback_stats: FeedbackStats;
  selector_metrics: SelectorMetrics;
  learning_health: LearningHealth;
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

function MLMetricsSection() {
  const [data, setData] = useState<MLMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMLMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/ai/ml-metrics');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setData(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch ML metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMLMetrics();
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-6 w-48 animate-pulse rounded bg-muted" />
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 animate-pulse rounded bg-muted" />
          ))}
        </div>
        <div className="h-48 animate-pulse rounded bg-muted" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
        Failed to load ML metrics: {error}
        <button onClick={fetchMLMetrics} className="ml-4 underline">
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const { feedback_stats, selector_metrics, learning_health } = data;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold">ML Monitoring</h2>
          <Badge variant="secondary">{feedback_stats.total_tools} tools tracked</Badge>
        </div>
        <button
          onClick={fetchMLMetrics}
          className="text-sm text-muted-foreground underline hover:text-foreground"
        >
          Refresh
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Feedback Entries
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {feedback_stats.total_entries.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">{feedback_stats.total_tools} tools</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              AI Selector Requests
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {selector_metrics.total_requests.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">
              {selector_metrics.avg_response_time_ms.toFixed(1)}ms avg
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Cost Saved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${selector_metrics.total_cost_saved.toFixed(4)}
            </div>
            <div className="text-xs text-muted-foreground">
              {selector_metrics.cost_optimization_enabled ? (
                <span className="text-green-600">Optimization enabled</span>
              ) : (
                <span className="text-muted-foreground">Optimization disabled</span>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Learning health */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <CardTitle className="text-sm font-medium">Top Performing Tools</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {learning_health.top_performing_tools.length === 0 ? (
              <div className="text-xs text-muted-foreground">No data yet</div>
            ) : (
              <ul className="space-y-1">
                {learning_health.top_performing_tools.map((tool) => (
                  <li key={tool} className="text-sm font-mono">
                    {tool}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              <CardTitle className="text-sm font-medium">Low Confidence Tools</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {learning_health.low_confidence_tools.length === 0 ? (
              <div className="text-xs text-muted-foreground">All tools healthy</div>
            ) : (
              <ul className="space-y-1">
                {learning_health.low_confidence_tools.map((tool) => (
                  <li key={tool} className="text-sm font-mono text-yellow-700">
                    {tool}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-blue-500" />
              <CardTitle className="text-sm font-medium">Top Task Types</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {learning_health.most_used_task_types.length === 0 ? (
              <div className="text-xs text-muted-foreground">No data yet</div>
            ) : (
              <ul className="space-y-1">
                {learning_health.most_used_task_types.map((t) => (
                  <li key={t} className="text-sm font-mono">
                    {t}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Model usage */}
      {selector_metrics.model_usage.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Model Usage</CardTitle>
            <CardDescription>Requests and token consumption per model</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {selector_metrics.model_usage.map((m) => (
                <div key={m.model} className="flex items-center justify-between py-2 text-sm">
                  <span className="font-mono font-medium">{m.model}</span>
                  <div className="flex gap-6 text-muted-foreground">
                    <span>{m.usage_count} calls</span>
                    <span>{m.total_tokens.toLocaleString()} tokens</span>
                    <span>${m.total_cost.toFixed(4)}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function AIDashboard() {
  return (
    <div className="container mx-auto space-y-8 py-8">
      <AIPerformanceDashboard />
      <ExperimentsSection />
      <MLMetricsSection />
    </div>
  );
}
