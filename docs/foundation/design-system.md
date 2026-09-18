# Seven2U — Design System

## Design Philosophy

Streaming platform companion. Dark-first (users watch series at night), with light mode support. Clean, spacious, content-focused. The series poster and metadata are the stars; UI stays out of the way.

## Color Palette

### Dark Mode (Primary)
- **Background**: `#0f0f0f` (near-black, cinema dark)
- **Surface**: `#1a1a2e` (deep navy-purple, streaming feel)
- **Surface Elevated**: `#232342` (cards, modals)
- **Primary**: `#e2b714` (gold, seventh art, warmth) 
- **Primary Hover**: `#f5cc3a`
- **Accent**: `#7c3aed` (violet, AI/insight moments)
- **Text Primary**: `#f0f0f0`
- **Text Secondary**: `#a0a0b0`
- **Text Muted**: `#6b6b80`
- **Success**: `#22c55e` (watched state)
- **Border**: `#2a2a40`

### Light Mode
- **Background**: `#fafafa`
- **Surface**: `#ffffff`
- **Surface Elevated**: `#f5f5f5`
- **Primary**: `#b8960e` (darker gold for contrast)
- **Accent**: `#6d28d9`
- **Text Primary**: `#1a1a2e`
- **Text Secondary**: `#4a4a60`
- **Border**: `#e5e5e5`

## Typography

- **Headings**: Inter, 600/700 weight — clean, modern, platform feel
- **Body**: Inter, 400 weight
- **Monospace** (episode codes, metadata): JetBrains Mono, 400
- **Scale**: 14/16/18/24/32/48px

## Spacing

Base unit: 4px. Scale: 4/8/12/16/24/32/48/64/96px.

## Border Radius

- **Cards**: 12px
- **Buttons**: 8px
- **Chips/Tags**: 6px
- **Posters**: 8px
- **Full round**: 9999px (avatars, pills)

## Shadows

Dark mode: minimal shadows, rely on surface color elevation.
Light mode: subtle `0 1px 3px rgba(0,0,0,0.08)` on cards.

## Components

### Search Bar
- Full-width, centered, prominent
- Subtle border, focus ring with primary color
- Debounced input (300ms)
- Loading spinner inside input on search

### Series Card (Search Results)
- Horizontal or grid layout
- Poster thumbnail (left or top)
- Title, year, genre chips
- Hover: subtle elevation/scale

### Series Detail
- Hero section: poster + title + genres + year
- AI Insight card: accent (violet) border, distinct from regular content
- Episodes grouped by season (collapsible accordion or tabs)
- Progress bar per season

### Episode Row
- Episode number + title
- Watched toggle (checkbox or icon)
- Comment icon with count
- AI Insight trigger button
- Watched state: success color indicator

### AI Insight Card
- Accent border (violet)
- Sparkle/brain icon
- Loading state: skeleton or pulse
- Fallback message if AI unavailable
- Distinct from user comments visually

### Comment Section
- Textarea + submit
- List of comments with timestamp
- Minimal, not social-media-styled

### Navigation
- Top bar: logo (Seven2U) + search
- Breadcrumb or back button on detail views
- No sidebar (single-surface app)

## Interaction States

- **Loading**: skeleton screens, not spinners (except inline search)
- **Error**: toast notification, retry option
- **Empty**: friendly illustration or message ("No results found", "Start searching for series")
- **Success**: brief green flash on watched toggle

## Responsive Breakpoints

- Mobile: < 640px (single column, stacked cards)
- Tablet: 640-1024px (2-column grid)
- Desktop: > 1024px (3-4 column grid, wider detail layout)

## Motion

- Transitions: 150ms ease-out (hover, focus)
- Page transitions: 200ms fade
- Accordion expand: 250ms ease
- Reduced motion: respect `prefers-reduced-motion`

## Iconography

Lucide icons — consistent, clean, MIT licensed. Key icons:
- Search (magnifying glass)
- Eye/EyeOff (watched toggle)
- MessageCircle (comments)
- Sparkles (AI insight)
- ChevronDown (accordion)
- ArrowLeft (back navigation)
