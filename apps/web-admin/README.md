# Forge MCP Gateway - Admin UI

A comprehensive Next.js admin dashboard for managing the Forge MCP Gateway, providing web-based management for virtual servers, feature toggles, usage analytics, and server templates.

## 🚀 Features

### Core Management
- **Virtual Server Management**: Enable/disable servers, view status, manage configurations
- **Feature Toggle Management**: Centralized feature flag management with forge-features CLI integration
- **Usage Analytics**: Real-time metrics, activity monitoring, and performance insights
- **Server Templates**: Template management for quick server deployment and configuration

### Technical Stack
- **Frontend**: Next.js 16 with App Router and TypeScript
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand for React state management
- **Data Fetching**: React Query for server state and caching
- **Backend**: Supabase for PostgreSQL database and authentication
- **UI Components**: Custom components with Radix UI primitives

## 🛠️ Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn
- Supabase project (for database and authentication)

### Installation

1. Clone the repository and navigate to the admin UI:
```bash
cd apps/web-admin
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.local.example .env.local
```

4. Configure Supabase:
```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

5. Run the development server:
```bash
npm run dev
```

6. Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── globals.css         # Global styles and Tailwind CSS
│   ├── layout.tsx          # Root layout with navigation
│   ├── page.tsx            # Dashboard page
│   ├── features/           # Feature toggles management
│   ├── servers/            # Virtual server management
│   ├── analytics/          # Usage analytics dashboard
│   └── templates/          # Server templates management
├── components/
│   ├── ui/                 # Reusable UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── switch.tsx
│   │   └── badge.tsx
│   ├── feature-toggles.tsx # Feature management component
│   └── navigation.tsx      # Navigation component
├── lib/
│   ├── supabase.ts         # Supabase client and database types
│   ├── store.ts            # Zustand state management stores
│   └── utils.ts            # Utility functions
└── types/                  # TypeScript type definitions
```

## 🔧 Configuration

### Database Schema
The admin UI uses the following Supabase tables:

- `users` - User authentication and profiles
- `virtual_servers` - Server configurations and status
- `server_templates` - Reusable server templates
- `usage_analytics` - Usage metrics and activity logs

### State Management
Zustand stores provide reactive state management:
- `useAuthStore` - Authentication state
- `useServerStore` - Virtual server management
- `useTemplateStore` - Server template management
- `useAnalyticsStore` - Usage analytics data

## 🎨 Design System

### Colors
- Primary: Blue tones for primary actions
- Secondary: Gray tones for secondary elements
- Success: Green for positive states
- Warning: Orange for caution states
- Error: Red for error states

### Components
All UI components follow a consistent design pattern:
- Built with Radix UI primitives
- Styled with Tailwind CSS
- Support for dark/light themes
- Fully responsive design

## 🔌 Integration Points

### MCP Gateway CLI
The admin UI integrates with the MCP gateway CLI:
- **Feature Toggles**: Uses `forge-features` command for centralized management
- **Server Management**: Integrates with `mcp server` commands
- **Templates**: Works with `mcp template` system

### Supabase Backend
- **Authentication**: JWT-based user authentication
- **Real-time Updates**: Real-time subscriptions for live data
- **Database**: PostgreSQL for persistent data storage

## 📊 Analytics and Monitoring

### Usage Metrics
- Server request counts and patterns
- Tool execution statistics
- User activity tracking
- Performance metrics

### Real-time Updates
- Live server status updates
- Real-time usage analytics
- Feature toggle changes
- System health monitoring

## 🚀 Deployment

### Development
```bash
npm run dev
```

### Build
```bash
npm run build
```

### Start Production
```bash
npm start
```

### Environment Variables
Required for production:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## 🔒 Security

- JWT-based authentication via Supabase
- Row Level Security (RLS) policies
- Environment variable protection
- HTTPS enforcement in production
- Input validation and sanitization

## 🧪 Testing

```bash
npm run test        # Run tests
npm run test:watch  # Watch mode
npm run lint        # Run ESLint
npm run type-check  # TypeScript checking
```

## 📚 Documentation

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [Radix UI Documentation](https://www.radix-ui.com/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the Forge MCP Gateway and follows the same license terms.
