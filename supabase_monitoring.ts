/**
 * Supabase monitoring utilities for Sentry integration
 * Provides comprehensive monitoring of Supabase operations across the UIForge ecosystem
 */

import { createClient, SupabaseClient } from "@supabase/supabase-js";

// Configuration interface
interface SupabaseMonitoringConfig {
  url: string;
  key: string;
  enableQueryLogging?: boolean;
  enablePerformanceTracking?: boolean;
  enableErrorTracking?: boolean;
  slowQueryThreshold?: number; // milliseconds
  maxQueryLength?: number;
}

// Default configuration
const DEFAULT_CONFIG: Partial<SupabaseMonitoringConfig> = {
  enableQueryLogging: true,
  enablePerformanceTracking: true,
  enableErrorTracking: true,
  slowQueryThreshold: 1000, // 1 second
  maxQueryLength: 1000,
};

export class SupabaseMonitor {
  private client: SupabaseClient;
  private config: Required<SupabaseMonitoringConfig>;
  private queryStats: Map<string, QueryStats> = new Map();

  constructor(config: SupabaseMonitoringConfig) {
    this.config = { ...DEFAULT_CONFIG, ...config } as Required<SupabaseMonitoringConfig>;
    this.client = createClient(config.url, config.key);
  }

  /**
   * Get the Supabase client with monitoring enabled
   */
  getClient(): SupabaseClient {
    return this.client;
  }

  /**
   * Monitor a Supabase query operation
   */
  async monitorQuery<T>(
    operation: string,
    table: string,
    queryFn: () => Promise<T>,
    query?: string
  ): Promise<T> {
    if (!this.config.enableQueryLogging) {
      return queryFn();
    }

    const startTime = Date.now();
    const queryKey = `${operation}.${table}`;

    try {
      const result = await queryFn();
      const duration = Date.now() - startTime;

      // Update query statistics
      this.updateQueryStats(queryKey, duration, true);

      // Log successful query
      this.logQuery(operation, table, query, duration, true);

      // Check for slow queries
      if (duration > this.config.slowQueryThreshold) {
        this.logSlowQuery(operation, table, query, duration);
      }

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;

      // Update query statistics
      this.updateQueryStats(queryKey, duration, false);

      // Log failed query
      this.logQuery(operation, table, query, duration, false, error as Error);

      throw error;
    }
  }

  /**
   * Monitor database connection health
   */
  async checkConnectionHealth(): Promise<ConnectionHealth> {
    const startTime = Date.now();

    try {
      // Simple health check query
      const { error } = await this.client.from('pg_tables').select('tablename').limit(1);
      const duration = Date.now() - startTime;

      return {
        healthy: !error,
        latency: duration,
        error: error?.message,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      const duration = Date.now() - startTime;

      return {
        healthy: false,
        latency: duration,
        error: (error as Error).message,
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Get database performance metrics
   */
  getPerformanceMetrics(): PerformanceMetrics {
    const stats = Array.from(this.queryStats.values());

    if (stats.length === 0) {
      return {
        totalQueries: 0,
        averageLatency: 0,
        slowQueries: 0,
        errorRate: 0,
        topSlowQueries: [],
        topErrorQueries: [],
      };
    }

    const totalQueries = stats.reduce((sum, stat) => sum + stat.totalQueries, 0);
    const totalLatency = stats.reduce((sum, stat) => sum + stat.totalLatency, 0);
    const totalErrors = stats.reduce((sum, stat) => sum + stat.errorCount, 0);
    const slowQueries = stats.filter(stat => stat.averageLatency > this.config.slowQueryThreshold);

    return {
      totalQueries,
      averageLatency: totalLatency / totalQueries,
      slowQueries: slowQueries.length,
      errorRate: totalErrors / totalQueries,
      topSlowQueries: stats
        .sort((a, b) => b.averageLatency - a.averageLatency)
        .slice(0, 10)
        .map(stat => ({
          operation: stat.operation,
          table: stat.table,
          averageLatency: stat.averageLatency,
          totalQueries: stat.totalQueries,
        })),
      topErrorQueries: stats
        .filter(stat => stat.errorCount > 0)
        .sort((a, b) => b.errorCount - a.errorCount)
        .slice(0, 10)
        .map(stat => ({
          operation: stat.operation,
          table: stat.table,
          errorCount: stat.errorCount,
          errorRate: stat.errorCount / stat.totalQueries,
        })),
    };
  }

  /**
   * Monitor table-specific operations
   */
  async monitorTableOperation<T>(
    table: string,
    operation: 'select' | 'insert' | 'update' | 'delete',
    queryFn: () => Promise<T>,
    query?: string
  ): Promise<T> {
    return this.monitorQuery(operation, table, queryFn, query);
  }

  /**
   * Monitor authentication operations
   */
  async monitorAuthOperation<T>(
    operation: 'signIn' | 'signUp' | 'signOut' | 'refresh',
    queryFn: () => Promise<T>
  ): Promise<T> {
    const startTime = Date.now();

    try {
      const result = await queryFn();
      const duration = Date.now() - startTime;

      this.logAuthOperation(operation, duration, true);

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;

      this.logAuthOperation(operation, duration, false, error as Error);

      throw error;
    }
  }

  /**
   * Monitor storage operations
   */
  async monitorStorageOperation<T>(
    operation: 'upload' | 'download' | 'delete' | 'list',
    path: string,
    queryFn: () => Promise<T>,
    fileSize?: number
  ): Promise<T> {
    const startTime = Date.now();

    try {
      const result = await queryFn();
      const duration = Date.now() - startTime;

      this.logStorageOperation(operation, path, duration, true, fileSize);

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;

      this.logStorageOperation(operation, path, duration, false, fileSize, error as Error);

      throw error;
    }
  }

  /**
   * Update query statistics
   */
  private updateQueryStats(queryKey: string, duration: number, success: boolean): void {
    const existing = this.queryStats.get(queryKey);

    if (existing) {
      existing.totalQueries++;
      existing.totalLatency += duration;
      existing.averageLatency = existing.totalLatency / existing.totalQueries;

      if (!success) {
        existing.errorCount++;
      }
    } else {
      const [operation, table] = queryKey.split('.');
      this.queryStats.set(queryKey, {
        operation,
        table,
        totalQueries: 1,
        totalLatency: duration,
        averageLatency: duration,
        errorCount: success ? 0 : 1,
      });
    }
  }

  /**
   * Log query execution
   */
  private logQuery(
    operation: string,
    table: string,
    query: string | undefined,
    duration: number,
    success: boolean,
    error?: Error
  ): void {
    const logData = {
      operation,
      table,
      query: this.sanitizeQuery(query || ''),
      duration,
      success,
      error: error?.message,
      timestamp: new Date().toISOString(),
    };

    // Send to Sentry as breadcrumb
    if (typeof window !== 'undefined' && window.Sentry) {
      window.Sentry.addBreadcrumb({
        category: 'supabase.query',
        message: `${operation} on ${table}`,
        level: success ? 'info' : 'error',
        data: logData,
      });
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`Supabase Query: ${operation} on ${table}`, logData);
    }
  }

  /**
   * Log slow query
   */
  private logSlowQuery(
    operation: string,
    table: string,
    query: string | undefined,
    duration: number
  ): void {
    const logData = {
      operation,
      table,
      query: this.sanitizeQuery(query || ''),
      duration,
      threshold: this.config.slowQueryThreshold,
      timestamp: new Date().toISOString(),
    };

    // Send to Sentry as warning
    if (typeof window !== 'undefined' && window.Sentry) {
      window.Sentry.addBreadcrumb({
        category: 'supabase.slow_query',
        message: `Slow query: ${operation} on ${table}`,
        level: 'warning',
        data: logData,
      });
    }

    console.warn(`Slow Supabase Query: ${operation} on ${table} (${duration}ms)`, logData);
  }

  /**
   * Log authentication operation
   */
  private logAuthOperation(
    operation: string,
    duration: number,
    success: boolean,
    error?: Error
  ): void {
    const logData = {
      operation,
      duration,
      success,
      error: error?.message,
      timestamp: new Date().toISOString(),
    };

    // Send to Sentry as breadcrumb
    if (typeof window !== 'undefined' && window.Sentry) {
      window.Sentry.addBreadcrumb({
        category: 'supabase.auth',
        message: `Auth ${operation}`,
        level: success ? 'info' : 'error',
        data: logData,
      });
    }

    console.log(`Supabase Auth: ${operation}`, logData);
  }

  /**
   * Log storage operation
   */
  private logStorageOperation(
    operation: string,
    path: string,
    duration: number,
    success: boolean,
    fileSize?: number,
    error?: Error
  ): void {
    const logData = {
      operation,
      path,
      duration,
      success,
      fileSize,
      error: error?.message,
      timestamp: new Date().toISOString(),
    };

    // Send to Sentry as breadcrumb
    if (typeof window !== 'undefined' && window.Sentry) {
      window.Sentry.addBreadcrumb({
        category: 'supabase.storage',
        message: `Storage ${operation} on ${path}`,
        level: success ? 'info' : 'error',
        data: logData,
      });
    }

    console.log(`Supabase Storage: ${operation} on ${path}`, logData);
  }

  /**
   * Sanitize query to remove sensitive information
   */
  private sanitizeQuery(query: string): string {
    if (!query) return '';

    // Truncate long queries
    if (query.length > this.config.maxQueryLength) {
      query = query.substring(0, this.config.maxQueryLength) + '...';
    }

    // Remove email addresses
    query = query.replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL]');

    // Remove API keys and tokens
    query = query.replace(/[A-Za-z0-9]{20,}/g, '[REDACTED]');

    // Remove password patterns
    query = query.replace(/password\s*=\s*'[^']*'/gi, "password='[REDACTED]'");

    return query;
  }

  /**
   * Reset query statistics
   */
  resetStats(): void {
    this.queryStats.clear();
  }

  /**
   * Get query statistics for a specific operation
   */
  getQueryStats(operation: string, table?: string): QueryStats | undefined {
    const key = table ? `${operation}.${table}` : operation;
    return this.queryStats.get(key);
  }

  /**
   * Get all query statistics
   */
  getAllQueryStats(): Map<string, QueryStats> {
    return new Map(this.queryStats);
  }
}

// Type definitions
interface QueryStats {
  operation: string;
  table: string;
  totalQueries: number;
  totalLatency: number;
  averageLatency: number;
  errorCount: number;
}

interface ConnectionHealth {
  healthy: boolean;
  latency: number;
  error?: string;
  timestamp: string;
}

interface PerformanceMetrics {
  totalQueries: number;
  averageLatency: number;
  slowQueries: number;
  errorRate: number;
  topSlowQueries: Array<{
    operation: string;
    table: string;
    averageLatency: number;
    totalQueries: number;
  }>;
  topErrorQueries: Array<{
    operation: string;
    table: string;
    errorCount: number;
    errorRate: number;
  }>;
}

// Global monitor instance
let globalMonitor: SupabaseMonitor | null = null;

/**
 * Initialize global Supabase monitor
 */
export function initializeSupabaseMonitor(config: SupabaseMonitoringConfig): SupabaseMonitor {
  globalMonitor = new SupabaseMonitor(config);
  return globalMonitor;
}

/**
 * Get global Supabase monitor
 */
export function getSupabaseMonitor(): SupabaseMonitor | null {
  return globalMonitor;
}

/**
 * Create a monitored Supabase client
 */
export function createMonitoredSupabaseClient(
  url: string,
  key: string,
  config?: Partial<SupabaseMonitoringConfig>
): SupabaseClient {
  const monitorConfig = { url, key, ...config };
  const monitor = new SupabaseMonitor(monitorConfig);

  // Store in global if not already set
  if (!globalMonitor) {
    globalMonitor = monitor;
  }

  return monitor.getClient();
}
