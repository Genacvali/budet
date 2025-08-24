# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Russian-language iOS-friendly Progressive Web Application (PWA) called "Бюджет — конверты" (Budget - Envelopes) that implements envelope budgeting methodology. The app helps users allocate their budget across different spending categories using both percentage-based and fixed amount allocations.

## Architecture

This is a single-page application with no build process or external dependencies:

- **Frontend**: Pure HTML/CSS/JavaScript (no frameworks)
- **Storage**: localStorage for persistence (key: `budget-ios-state`)
- **PWA**: iOS-optimized service worker for offline functionality
- **Deployment**: Static files served directly, works on GitHub Pages subpaths

### Key Files Structure

- `index.html` - Complete application with embedded CSS and JavaScript
- `manifest.json` - PWA manifest with relative paths for GitHub Pages (`start_url` and `scope` = ".")
- `service-worker.js` - Service worker with cache version `budget-ios-v1`
- `README.txt` - Russian deployment instructions
- `icons/` - PWA icons including Apple touch icon placeholders

### iOS PWA Optimizations

**Meta Tags**:
- `apple-mobile-web-app-capable="yes"` - Enables standalone mode
- `apple-mobile-web-app-status-bar-style="black-translucent"` - Status bar styling
- `apple-mobile-web-app-title="Бюджет"` - App title on home screen
- `viewport-fit=cover, user-scalable=no` - Handles notch and prevents zoom

**CSS Safe Areas**:
- Uses `env(safe-area-inset-*)` for proper spacing around iPhone notch/gesture areas
- 16px input font sizes to prevent iOS zoom
- Dark theme optimized for mobile viewing

**Install Hint**:
- Shows Safari installation hint once (`installHint` component)
- Guides users to "Share → Add to Home Screen"

## UI Structure

### Three-Tab Navigation
- **Plan** (`#view-plan`) - Budget categories and allocations
- **Operations** (`#view-ops`) - Transaction journal with filters
- **More** (`#view-settings`) - Settings and data management

### Key Components
- **FAB** (`#fabAdd`) - Floating action button for quick transaction entry
- **Transaction Modal** (`#txModal`) - Category-specific transaction CRUD
- **Bottom Tabs** - Mobile-optimized navigation with `.active` state

## Data Model

The application uses localStorage under key `budget-ios-state`:

```javascript
{
  budget: Number,           // Total budget amount
  rows: Array,             // Categories with sections
  tx: Object,              // Transactions by category ID
  quick: Array,            // Quick amounts (e.g. [-500, -1000, -2000])
  monthFilter: String,     // Current month filter (YYYY-MM or "")
  currency: String         // Currency symbol (default "₽")
}
```

### Budget Calculations
- **Base**: `budget - Σ(fixed rub amounts)`
- **Plan per category**: `rub` (if set) OR `pct/100 * base`
- **Spent per category**: Sum of transactions in selected period
- **Remaining**: `plan - spent`

## Development Commands

No build system required. Development workflow:

1. **Serve locally**: `python -m http.server` or VS Code Live Server
2. **Testing**: Manual testing in browser and iOS Safari
3. **Cache updates**: Increment `CACHE` version in `service-worker.js` when updating assets
4. **Deployment**: Upload to static hosting (GitHub Pages ready with relative paths)

## Import/Export Features

### CSV Format
- Headers: `date,category,amount,note` (supports Russian equivalents)
- Delimiters: `,` or `;` (auto-detected)
- Auto-creates missing categories during import
- Export filters by selected time period

### JSON Format
- Complete application state export/import
- Preserves all data including transactions and settings

## Key Technical Considerations

### GitHub Pages Compatibility
- Uses relative paths (`"."`) for `start_url` and `scope`
- Service worker registration: `./service-worker.js`
- Works seamlessly on subpaths like `/budet/`

### Mobile UX Patterns
- Large touch targets (minimum 44px)
- Swipe-friendly card layouts
- Context-aware input types (`inputmode="decimal"`)
- Prevents accidental zoom with `user-scalable=no`

### Performance
- Single HTML file with embedded assets
- Efficient localStorage operations
- Service worker caching for offline use
- No external dependencies or build process

## Potential Enhancements

1. **Theming**: Light theme toggle with `prefers-color-scheme`
2. **Drag & Drop**: Category reordering with fixed essential categories
3. **Quick Actions**: In-row spending buttons for categories
4. **Sync**: Webhook integration for external data sync
5. **Reports**: Weekly/monthly summaries and charts
6. **Icons**: Replace placeholder icons with branded assets