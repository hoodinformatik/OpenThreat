# OpenThreat Frontend

Modern Next.js 14 frontend for the OpenThreat platform.

## Features

- ✅ **Dashboard** - KPIs, severity distribution, top exploited vulnerabilities
- ✅ **Vulnerability List** - Paginated list with filters and sorting
- ✅ **Vulnerability Detail** - Complete CVE information
- ✅ **Advanced Search** - Multi-criteria search with 9+ filters
- ✅ **RSS Feeds** - Subscribe to vulnerability feeds
- ✅ **Responsive Design** - Works on mobile, tablet, and desktop
- ✅ **Real-time Data** - Direct API integration with caching

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **UI Components**: Custom components (shadcn/ui style)
- **Icons**: Lucide React
- **State**: React Hooks

## Getting Started

### Prerequisites

- Node.js 18+
- Running OpenThreat API (port 8001)

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Edit .env.local with your API URL
# NEXT_PUBLIC_API_URL=http://127.0.0.1:8001
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build

```bash
npm run build
npm start
```

## Pages

### Dashboard (`/`)
- Total vulnerabilities count
- Exploited vulnerabilities count
- Critical/High severity counts
- Recent updates
- Severity distribution chart
- Top 5 exploited vulnerabilities
- Top 5 recent vulnerabilities

### Vulnerabilities List (`/vulnerabilities`)
- Paginated list (20 per page)
- Filters:
  - Severity (Critical, High, Medium, Low)
  - Exploitation status
  - Sort by (Priority, CVSS, Published, Modified)
- Click to view details

### Vulnerability Detail (`/vulnerabilities/[cveId]`)
- Complete CVE information
- CVSS score and vector
- Priority score
- CWE IDs
- Affected vendors and products
- References with tags
- Publication and modification dates

### Advanced Search (`/search`)
- Text search (CVE ID, title, description)
- Severity filter
- Exploitation status filter
- Vendor filter
- Product filter
- CVSS score range (min/max)
- Publication date range
- Real-time results

### RSS Feeds (`/feeds`)
- All recent vulnerabilities feed
- Exploited vulnerabilities feed
- Critical vulnerabilities feed
- Copy feed URLs
- Popular RSS readers list

## API Integration

The frontend communicates with the FastAPI backend via REST API:

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';

// Example: Fetch vulnerabilities
const res = await fetch(`${API_URL}/api/v1/vulnerabilities?page=1&page_size=20`);
const data = await res.json();
```

## Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001
```

## Project Structure

```
frontend/
├── app/                        # Next.js App Router
│   ├── page.tsx               # Dashboard
│   ├── layout.tsx             # Root layout
│   ├── globals.css            # Global styles
│   ├── vulnerabilities/
│   │   ├── page.tsx          # List page
│   │   └── [cveId]/
│   │       └── page.tsx      # Detail page
│   ├── search/
│   │   └── page.tsx          # Search page
│   └── feeds/
│       └── page.tsx          # RSS feeds page
├── components/
│   ├── navigation.tsx         # Main navigation
│   └── ui/                    # UI components
│       ├── card.tsx
│       ├── badge.tsx
│       └── button.tsx
├── lib/
│   ├── api.ts                 # API client
│   └── utils.ts               # Utility functions
├── public/                    # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## Styling

### TailwindCSS Classes

Common patterns used:

```tsx
// Card
<Card className="hover:shadow-md transition-shadow">

// Badge with severity color
<Badge className={getSeverityBadgeColor(severity)}>

// Button variants
<Button variant="outline" size="sm">

// Grid layout
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
```

### Color Scheme

- **Primary**: Blue (#2563eb)
- **Critical**: Red (#dc2626)
- **High**: Orange (#ea580c)
- **Medium**: Yellow (#ca8a04)
- **Low**: Blue (#2563eb)
- **Background**: Gray (#f9fafb)

## Performance

- **Server Components**: Default for data fetching
- **Client Components**: Only for interactivity
- **Caching**: 60s revalidation for most pages
- **No-cache**: Search results (dynamic)

## Accessibility

- Semantic HTML
- ARIA labels where needed
- Keyboard navigation
- Focus states
- Color contrast (WCAG AA)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### API Connection Issues

If you see "fetch failed" errors:

1. Check API is running: `curl http://127.0.0.1:8001/health`
2. Update `.env.local` with correct API URL
3. Use `127.0.0.1` instead of `localhost` (Windows IPv6 issue)
4. Restart dev server after changing `.env.local`

### Styling Issues

If TailwindCSS classes don't work:

1. Check `tailwind.config.ts` content paths
2. Ensure `globals.css` is imported in `layout.tsx`
3. Clear `.next` cache: `rm -rf .next`
4. Restart dev server

## Contributing

1. Follow existing code style
2. Use TypeScript types
3. Test on multiple screen sizes
4. Ensure accessibility
5. Update documentation

## License

Apache-2.0 (same as main project)
