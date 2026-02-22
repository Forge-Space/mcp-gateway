# Sentry Integration with Supabase for UIForge Ecosystem

This document provides comprehensive guidance for integrating Sentry error tracking and performance monitoring with Supabase across the UIForge ecosystem.

## Overview

The Sentry integration provides:
- **Error Tracking**: Capture and analyze errors across all applications
- **Performance Monitoring**: Track application performance and database queries
- **Supabase Integration**: Monitor Supabase database operations, authentication, and storage
- **Distributed Tracing**: Track requests across microservices
- **Real-time Alerts**: Get notified about critical issues immediately

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Sentry UI     │    │  Self-Hosted    │    │   Supabase      │
│   (Dashboard)   │◄──►│   Sentry        │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ uiforge-webapp  │    │   mcp-gateway    │    │   uiforge-mcp   │
│   (Next.js)     │    │    (Python)     │    │   (Node.js)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Set up Self-Hosted Sentry

```bash
cd /Users/lucassantana/Desenvolvimento/mcp-gateway/sentry
cp .env.example .env
# Update .env with your configuration
./setup.sh
```

### 2. Configure Environment Variables

Copy the appropriate environment template for each project:

```bash
# For mcp-gateway
cp .env.sentry.example .env.local

# For uiforge-mcp  
cp .env.sentry.example .env.local

# For uiforge-webapp
cp .env.sentry.example .env.local
```

Update each `.env.local` file with your actual Sentry and Supabase credentials.

### 3. Install Dependencies

```bash
# mcp-gateway (Python)
pip install sentry-sdk[fastapi] structlog psycopg2-binary

# uiforge-mcp (Node.js)
npm install @sentry/node @sentry/tracing @supabase/sentry-js-integration

# uiforge-webapp (Next.js)
npm install @sentry/nextjs @supabase/sentry-js-integration
```

### 4. Initialize Sentry

The integration is automatically initialized when the applications start, provided the environment variables are configured.

## Configuration

### Sentry Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `SENTRY_DSN` | Sentry Data Source Name | Yes |
| `SENTRY_ORG` | Sentry organization | Optional |
| `SENTRY_PROJECT` | Sentry project name | Optional |
| `SENTRY_ENVIRONMENT` | Environment (development/staging/production) | Optional |
| `SENTRY_SAMPLE_RATE` | Transaction sampling rate (0-1) | Optional |
| `SENTRY_PROFILES_SAMPLE_RATE` | Profiling sampling rate (0-1) | Optional |

### Supabase Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase anonymous key | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Optional |

### Next.js Public Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_SENTRY_DSN` | Public Sentry DSN for client-side | Yes |
| `NEXT_PUBLIC_SUPABASE_URL` | Public Supabase URL | Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public Supabase anonymous key | Yes |

## Integration Details

### mcp-gateway (Python)

The Python integration includes:

- **FastAPI Integration**: Automatic request/response tracking
- **Structured Logging**: Integration with structlog
- **Database Monitoring**: SQLAlchemy integration for database queries
- **Service Lifecycle**: Monitor service start/stop/sleep/wake events
- **MCP Operations**: Track MCP tool execution performance

Key files:
- `tool_router/sentry_integration.py` - Main Sentry configuration
- `service-manager/service_manager.py` - Service lifecycle monitoring

### uiforge-mcp (Node.js)

The Node.js integration includes:

- **MCP Server Monitoring**: Track tool execution and server performance
- **Supabase Integration**: Monitor database operations and authentication
- **AI Operations**: Track AI model usage and performance
- **Figma Operations**: Monitor Figma API calls and design operations

Key files:
- `src/lib/sentry.ts` - Main Sentry configuration
- `src/index.ts` - Application initialization

### uiforge-webapp (Next.js)

The Next.js integration includes:

- **Client-Side Monitoring**: Browser error tracking and performance
- **Server-Side Monitoring**: API route and server function monitoring
- **User Interactions**: Track UI interactions and user behavior
- **Page Performance**: Monitor page load times and Core Web Vitals

Key files:
- `src/lib/sentry.ts` - Shared Sentry utilities
- `src/lib/sentry.client.ts` - Client-side configuration
- `src/lib/sentry.server.ts` - Server-side configuration
- `next.config.js` - Webpack integration

## Supabase Monitoring

### Database Operations

Monitor all database operations with automatic query logging:

```typescript
import { getSupabaseMonitor } from './lib/supabase_monitoring';

const monitor = getSupabaseMonitor();
const result = await monitor.monitorQuery(
  'select',
  'users',
  () => supabase.from('users').select('*'),
  'SELECT * FROM users WHERE active = true'
);
```

### Authentication Operations

Track authentication events:

```typescript
const result = await monitor.monitorAuthOperation(
  'signIn',
  () => supabase.auth.signInWithPassword(email, password)
);
```

### Storage Operations

Monitor file operations:

```typescript
const result = await monitor.monitorStorageOperation(
  'upload',
  'avatars/user123.jpg',
  () => supabase.storage.from('avatars').upload('user123.jpg', file),
  file.size
);
```

## Performance Monitoring

### Database Performance

Track slow queries and database health:

```typescript
const metrics = monitor.getPerformanceMetrics();
console.log('Average query latency:', metrics.averageLatency);
console.log('Slow queries:', metrics.slowQueries);
console.log('Error rate:', metrics.errorRate);
```

### Connection Health

Monitor database connectivity:

```typescript
const health = await monitor.checkConnectionHealth();
if (!health.healthy) {
  console.error('Database connection issue:', health.error);
}
```

## Error Tracking

### Custom Error Context

Add rich context to errors:

```typescript
import { captureException } from './lib/sentry';

try {
  // Your code here
} catch (error) {
  captureException(error, {
    operation: 'user_registration',
    userId: user.id,
    metadata: { plan: 'premium' }
  });
}
```

### Supabase Error Handling

Capture Supabase-specific errors:

```typescript
import { captureSupabaseError } from './lib/sentry';

try {
  await supabase.from('users').insert(userData);
} catch (error) {
  captureSupabaseError(error, 'insert', 'users', query);
}
```

## Alerting and Dashboards

### Setting Up Alerts

1. **Navigate to Sentry Dashboard**: Access your self-hosted Sentry instance
2. **Create Alert Rules**: Set up alerts for:
   - High error rates
   - Performance degradation
   - Database connection issues
   - Authentication failures

### Recommended Alerts

| Alert Type | Condition | Severity |
|------------|-----------|----------|
| Error Rate | Error rate > 5% over 5 minutes | Critical |
| Performance | P95 latency > 2 seconds | Warning |
| Database | Connection failures > 3/minute | Critical |
| Authentication | Failed sign-ins > 10/minute | Warning |

### Dashboard Configuration

Create dashboards to monitor:

- **Error Overview**: Total errors, error rate, top issues
- **Performance**: Response times, database queries, slow operations
- **Database**: Query performance, connection health, table statistics
- **User Activity**: Authentication events, user interactions

## Best Practices

### 1. Environment Configuration

- Use separate Sentry projects for each environment
- Configure appropriate sampling rates for production
- Never commit sensitive credentials to version control

### 2. Error Handling

- Add meaningful context to errors
- Use structured logging for better searchability
- Filter out expected errors to reduce noise

### 3. Performance Monitoring

- Monitor database query performance
- Track API response times
- Set appropriate thresholds for alerts

### 4. Security

- Sanitize sensitive data before sending to Sentry
- Use environment variables for configuration
- Regularly review Sentry access permissions

## Troubleshooting

### Common Issues

1. **Sentry not receiving events**
   - Check DSN configuration
   - Verify network connectivity
   - Review Sentry logs

2. **Supabase integration not working**
   - Verify Supabase credentials
   - Check Supabase integration initialization
   - Review browser console for errors

3. **Performance monitoring not working**
   - Verify tracing configuration
   - Check sampling rates
   - Review transaction names

### Debug Mode

Enable debug mode for troubleshooting:

```typescript
// In development
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  debug: true,
  environment: 'development'
});
```

## Migration Guide

### From Basic Error Tracking

1. **Install Sentry SDK**: Add appropriate packages
2. **Configure Environment**: Set up environment variables
3. **Initialize Sentry**: Add initialization code
4. **Add Context**: Enhance error reporting with context
5. **Enable Performance**: Add performance monitoring

### From Third-Party Services

1. **Export Data**: Export existing error data if possible
2. **Update Configuration**: Point applications to new Sentry instance
3. **Test Integration**: Verify error reporting works
4. **Update Dashboards**: Recreate monitoring dashboards
5. **Update Alerts**: Migrate alert configurations

## Support

For issues with the Sentry integration:

1. Check the [Sentry Documentation](https://docs.sentry.io/)
2. Review the [Supabase Integration Guide](https://supabase.com/docs/guides/platform/sentry)
3. Check the UIForge documentation
4. Create an issue in the UIForge repository

## Security Considerations

- **Data Privacy**: Ensure no sensitive data is sent to Sentry
- **Access Control**: Limit Sentry dashboard access to authorized users
- **Network Security**: Use HTTPS for all Sentry communications
- **Compliance**: Ensure compliance with data protection regulations

## Maintenance

### Regular Tasks

- **Review Error Trends**: Weekly review of error patterns
- **Update Dependencies**: Keep Sentry SDKs up to date
- **Monitor Costs**: Track Sentry usage and costs
- **Backup Configuration**: Backup Sentry configuration and data

### Performance Optimization

- **Sampling Rates**: Adjust sampling rates based on traffic
- **Filter Rules**: Refine error filtering to reduce noise
- **Retention Policies**: Set appropriate data retention periods
- **Index Optimization**: Optimize Sentry indexes for better performance
