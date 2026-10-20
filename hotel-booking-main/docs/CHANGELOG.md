# Changelog

Only changes verified in the current work session are recorded. No dates are invented for earlier repository history.

## 2026-10-20 — Chartreuse primary actions

- Changed all primary application actions to Chartreuse `#D9ED48` with Soft Charcoal `#24251F` text.
- Applied the same primary-action treatment to search, booking, authentication, dashboard, and Django admin buttons.
- Added a Soft Charcoal hover/focus state with Pure White text for clear interaction feedback.
- Corrected the homepage search surface and hero kicker contrast after the global button update.

## 2026-10-20 — Enforced four-colour interface palette

- Standardized every local stylesheet and inline chart configuration on Chartreuse `#D9ED48`, Soft Charcoal `#24251F`, Warm Ivory `#F6F5EF`, and Pure White `#FFFFFF`.
- Removed legacy mint, green, blue, lavender, red, amber, gray, and beige tokens from public pages, dashboards, authentication, toasts, status treatments, and Django admin styling.
- Retained transparency derived only from the approved charcoal, white, and chartreuse colors for shadows, overlays, focus rings, and chart fills.
- Preserved hotel photography as content imagery; the four-colour restriction applies to interface styling and components.
- Rechecked the homepage, preferences, and customer dashboard visually after palette enforcement.
- Source audit found no unapproved hexadecimal color tokens in `static/css` or templates.
- `manage.py check` passed and all 42 automated tests passed.

## 2026-10-20 — Zinc surfaces, borderless cards, and compact heroes

- Standardized the application canvas on zinc-50/100 tones with zinc-900 primary actions and zinc-200 secondary actions.
- Removed visible component borders in favor of spacing, tonal separation, and low-elevation shadows.
- Improved button hover, focus, and pressed hierarchy while preserving accessible keyboard focus rings.
- Reduced public and dashboard hero height; the full homepage hero and search action now fit in the initial desktop viewport.
- Redesigned the preferences form with a charcoal explanation panel, lime matching label, borderless fields, and clearer two-zone hierarchy.
- Improved My Trips booking rows and empty state, dashboard cards, room listing filters, room details, and recommendation cards.
- Visually inspected the homepage, preferences, My Trips, dashboard, room listing, room detail, and recommendations pages.
- Re-ran `manage.py check` and all 42 automated tests successfully.

## 2026-10-20 — Editorial high-contrast interface refinement

- Replaced the remaining green-led visual language with a near-white/light-gray canvas, charcoal primary surfaces, electric-lime interaction accents, and soft lavender reserved for explainable recommendations.
- Rebuilt the homepage as an editorial split hero with large photography, oversized high-contrast typography, a floating search surface, compact pill labels, and circular directional actions.
- Added a structured featured-stays presentation, dark recommendation story panel, and varied three-step process cards.
- Strengthened room-list filters, room-card imagery, detail-page containers, booking hierarchy, and component boundaries without changing forms, URLs, or backend behavior.
- Retained semantic success, warning, error, information, and recommendation colors where status meaning is required.
- Visually inspected the homepage, dashboard, and room listing in the running authenticated application.
- Re-ran `manage.py check` and all 42 automated tests successfully.

## 2026-10-20 — Neutral visual system and unified customer workspace

- Added `static/css/refresh.css` as an override layer for the existing component system.
- Rebalanced the interface toward warm porcelain, white, stone, soft blue, lilac, sand, and restrained blush surfaces; forest green remains the brand, primary-action, focus, and success colour.
- Moved My Trips, booking detail/checkout, recommendations, preferences, and profile editing into the shared dashboard shell without changing URLs or backend behavior.
- Added route-aware sidebar states for booking, recommendation, preference, and profile pages.
- Removed the dashboard footer and corrected duplicate nested `main`/`main-content` landmarks.
- Centered dashboard workspace containers at a consistent maximum width.
- Visually inspected the dashboard, trip list, and booking detail in the running authenticated application.
- Re-ran `manage.py check` and all 42 automated tests successfully.

## 2026-10-20

### UI/UX

- Established the Mint & Seafoam design system across public pages, authentication, rooms, bookings, recommendations, dashboards, and Django Admin.
- Added responsive room cards, image fallbacks, form states, empty states, status badges, pagination, dashboard sidebar/off-canvas navigation, and local authentication photography.
- Reorganized travel preferences and implemented split-screen multi-step registration.
- Compacted the signup flow into a viewport-height layout, moving password guidance into an accessible disclosure so the normal form fits without page scrolling on tested desktop and mobile viewports.
- Replaced layout-shifting Django messages with compact, accessible, fixed-position toasts.

### Backend functionality

- Added room inventory fields, uploaded/URL images, identifiers, statuses, capacity, pricing, and timestamps through preserved migrations.
- Implemented authenticated booking creation/history/detail/cancellation with server pricing and availability validation.
- Added customer and staff dashboard data services, date filters, trends, search, and pagination.
- Added username availability checking with Django username validation and session throttling.

### Security

- Restricted booking objects to their owner and staff dashboard routes to staff accounts.
- Kept logout and cancellation POST-only with CSRF protection.
- Required environment secrets in production and enabled secure production cookie, redirect, and HSTS settings.
- Prevented customer control of booking price, room ownership, reference, and status fields.

### Recommendation engine

- Implemented configurable deterministic weighted content scoring with capacity/date hard constraints.
- Added per-feature breakdowns, explanations, deterministic tie-breaking, missing-preference behavior, and an evaluation command.

### Testing

- Expanded the suite to 42 passing tests covering authentication, notification rendering, rooms, booking rules and permissions, dashboards, and recommendations.
- Verified Django checks, migration consistency, dependency consistency, desktop/mobile rendering, and browser console output.

### Documentation

- Expanded `README.md` and added architecture, recommendation, testing, changelog, and implementation-report documents.

### Dependencies and configuration

- Pinned Django 4.2.30 and Pillow 11.3.0.
- Added configurable debug, secret, allowed-host, and email-backend settings.
- No JavaScript notification dependency was added; the project uses a small vanilla manager.
