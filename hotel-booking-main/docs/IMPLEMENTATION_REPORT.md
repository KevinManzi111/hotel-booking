# Staywise Final Implementation Report

## Primary-action update — 2026-10-20

Primary buttons now use Chartreuse `#D9ED48` with Soft Charcoal `#24251F` text throughout public, authenticated, booking, authentication, and Django admin interfaces. Hover and keyboard-focus interaction reverses to Soft Charcoal with Pure White text while remaining within the approved four-colour palette.

## Four-colour palette enforcement — 2026-10-20

All non-photographic interface styling now uses one of four approved colors: Chartreuse `#D9ED48`, Soft Charcoal `#24251F`, Warm Ivory `#F6F5EF`, or Pure White `#FFFFFF`. Alpha variants of those same colors are used only for shadows, overlays, chart fills, and focus treatment.

Chartreuse identifies selected navigation, recommendation labels, confirmed states, profile marks, and special directional actions. Soft Charcoal provides headings, body copy, primary buttons, navigation contrast, dark feature panels, and icons. Warm Ivory is the main application canvas and supporting-panel tone. Pure White is reserved for cards, forms, booking panels, navigation bars, and content surfaces.

Previous semantic hues were removed. Status labels continue to communicate their meaning through text, icons, and label names rather than color alone, maintaining usability within the strict palette. Hotel photography is intentionally unchanged because it is database content rather than interface styling.

A source audit confirmed no unapproved hexadecimal colors remain in local styles or templates. Visual checks covered the homepage, preferences, and customer dashboard. Django checks passed and all 42 automated tests remained successful.

## Zinc and borderless component refinement — 2026-10-20

The visual foundation now uses zinc-50 and zinc-100 canvases, white content surfaces, zinc-900 primary actions, and zinc-200 secondary actions. Visible card and panel outlines were removed; hierarchy is instead communicated through rounded geometry, spacing, tonal contrast, and restrained shadows. Electric lime remains a controlled accent for current navigation, selected identity elements, success states, and directional actions.

Hero sections were compressed and rebalanced so page purpose and primary actions appear earlier. The complete homepage hero—including the search surface—is visible in the initial desktop viewport. Dashboard page heroes now use compact spacing and no decorative divider border.

The travel-preferences page received a dedicated layout refinement with a dark explanatory column, high-contrast matching label, borderless input treatment, clearer amenities grouping, and an elevated white form surface. My Trips now uses more substantial booking rows and a purpose-built zinc empty state rather than a large undifferentiated blank region.

Visual inspection covered the homepage, customer dashboard, preferences, My Trips, room listing, room detail, and recommendations pages. Django system checks passed and all 42 automated tests remained green.

## Editorial UI refinement — 2026-10-20

The interface now follows a light editorial hospitality direction informed by the supplied references: near-white and light-gray backgrounds, high-contrast charcoal typography, generous image crops, modular rounded containers, and one controlled electric-lime accent. Lavender remains the dedicated recommendation colour so algorithmic explanations stay visually distinct. Green is no longer the dominant brand or background colour.

The public homepage was structurally redesigned rather than merely recoloured. It now uses an asymmetric image-and-copy hero, a floating search bar, compact metadata, circular actions, image-forward stay cards, a high-contrast recommendation panel, and varied process cards. Existing database content, Django forms, routes, authentication, search parameters, and recommendation links are unchanged.

The shared component layer also improves room listings, filters, detail pages, dashboards, forms, and booking surfaces. Container borders and low-elevation shadows now separate content from the almost-white canvas without heavy colour fills.

Verified after implementation:

- `python manage.py check`: no issues.
- `python manage.py test`: 42 tests passed.
- Desktop visual inspection: homepage, customer dashboard, and room listing rendered correctly with the new hierarchy and palette.
- Existing authenticated content, search fields, recommendation actions, and dashboard navigation remained visible and operational.

## Visual-system refinement — 2026-10-20

The customer workspace now behaves as one coherent application surface. Account-owned workflows retain the sidebar and top bar, and load their existing server-rendered content in the centered dashboard workspace. Public discovery pages continue to use the public navigation shell.

The palette was rebalanced to prevent green from becoming a background wash. Warm neutral canvas and stone surfaces establish hierarchy; soft blue communicates information, lilac identifies recommendation content, sand supports profile and secondary context, and blush distinguishes cancelled or negative summaries. Forest green is intentionally concentrated on primary actions, the brand mark, keyboard focus, and confirmed or success states.

Verification performed after the change:

- `python manage.py check` using the project virtual environment: no issues.
- `python manage.py test` using the project virtual environment: 42 tests passed.
- Authenticated visual inspection at desktop width: dashboard, trip list, and booking detail rendered with the sidebar present and centered content.
- Browser console review: no application-origin warnings or errors were observed; captured errors came from an unrelated installed Chrome extension.
- A mobile DOM and accessibility inspection confirmed the responsive page retained navigation, top-bar actions, booking content, and semantic headings. The browser extension's screenshot viewport override did not produce a reliable narrow visual capture, so mobile visual verification remains a recommended device pass.

## 1. Executive summary

Staywise is an implemented Django hotel room discovery, booking, dashboard, and explainable recommendation project. The current build uses real ORM data, authenticated ownership boundaries, server-derived prices, interval availability, and deterministic preference matching. The complete automated suite passes; important desktop and mobile flows have been inspected manually. Limitations remain around SQLite concurrency, external frontend CDNs, production email/deployment, and absence of measured coverage or load testing.

## 2. Objectives and requirements

The project aims to let guests discover available rooms, securely book and manage stays, save preferences, understand ranked recommendations, and review personal activity. Staff need protected operational metrics and access to inventory, booking, and customer management. The mandated stack—Python, Django, SQLite, Django templates, HTML, CSS, vanilla JavaScript, and Bootstrap 5—is preserved.

## 3. Feature status

| Feature | Status | Evidence/qualification |
| --- | --- | --- |
| Registration, login/logout, profile, password reset | Implemented and verified | Django tests and browser signup/login checks; production email provider not configured. |
| Multi-step signup and username feedback | Implemented and verified | One Django form, JS presentation, POST JSON endpoint, tests and browser checks. |
| Room inventory and discovery | Implemented and verified | ORM filters, pagination, date availability, room tests. |
| Booking, price, overlap, cancellation, ownership | Implemented and verified | Model/view logic and booking tests. SQLite concurrency limitation remains. |
| Explainable weighted recommendations | Implemented and verified | Service tests, UI breakdown, evaluator output. This is not trained ML. |
| Customer dashboard | Implemented and verified | Owned ORM queries, metrics, empty states, recommendations; desktop/mobile checked. |
| Staff dashboard and management | Implemented and verified | Server metrics, filtering, pagination, staff decorator, Django Admin; Chart.js uses CDN. |
| Toast notifications | Implemented and verified | Four levels rendered in tests; desktop/mobile placement and dismissal checked. |
| Production deployment | Not implemented | Security switches exist, but no production server, PostgreSQL, storage, SMTP, or CI/CD configuration is included. |

## 4. Architecture

The project is a server-rendered monolith split into `accounts`, `hotels`, `bookings`, and `recommendations`. Views orchestrate forms/services and render templates. Forms validate request input; model methods protect booking invariants; services encapsulate staff metrics and recommendation scoring. SQLite stores local data. See `ARCHITECTURE.md` for diagrams and boundaries.

## 5. UI/UX and design system

CSS variables in `static/css/site.css` define Mint & Seafoam colors, typography, radii, shadows, and status colors. Shared public and dashboard templates provide consistent navigation. Reusable partials render fields, messages, room cards, booking rows, pagination, and footer. Layouts include keyboard focus, responsive grids, mobile navigation, empty states, loading states, and local image fallbacks. Signup-specific density rules in `static/css/signup.css` keep the normal three-step form within tested desktop and mobile viewports while retaining expandable password guidance. `static/css/toasts.css` isolates fixed notification behavior from legacy page styles.

## 6. Authentication and validation

`SignUpForm` extends `UserCreationForm`, retaining Django password validators and username uniqueness. Email uniqueness is case-insensitive. The signup wizard changes only presentation: all values remain in one form until final POST, so Django repopulates submitted values and displays returned errors. JavaScript activates the step containing an error. Username availability reuses the form's username field validation, returns no account details, accepts POST with CSRF, and applies a per-session limit of 30 checks per minute. Database uniqueness remains authoritative.

Django auth views provide login/logout/password reset. Development reset email is printed to the console; production defaults to SMTP and needs real configuration.

## 7. Booking and availability

`BookingForm` exposes only dates, guests, and special requests. The view assigns the authenticated user and selected room. `Booking.save()` calls `full_clean()`, verifies dates/capacity/confirmed overlap, and calculates nights × room rate. The original total persists when room pricing later changes unless booking room/dates change. Detail and cancellation query by both booking ID and current user. Cancellation is allowed only for pending/confirmed future stays.

`transaction.atomic()` and `select_for_update(Room)` are used during submission. SQLite's row-lock limitation means strong simultaneous-write protection is only partially implemented; PostgreSQL is required before claiming production race safety.

## 8. Recommendation algorithm and evaluation

Five normalized scores—budget, location, room type, amenities, and capacity—use 30/20/20/20/10 percent weights. Status, capacity, and requested-date availability are hard filters. Results expose contributions and reasons, then sort by score, price, and ID. The current evaluator measured two saved profiles and catalogue coverage 1.0 on the local three-room catalogue; it did not measure relevance accuracy. See `RECOMMENDATION_ENGINE.md`.

## 9. Dashboards

The customer dashboard queries only `request.user.bookings`, divides them into upcoming, past, and cancelled groups, calculates counts, and requests three recommendations. The staff dashboard is protected by `staff_member_required`; `dashboard_metrics()` calculates room counts, period availability, status totals, cancellations, booked revenue, customer count, and date-series values. Recent booking search uses reference, username, email, room name, and identifier and paginates 12 rows.

Revenue is confirmed/completed booking value, not payment settlement. Availability is active inventory without confirmed overlap in the selected period.

## 10. Security measures

- CSRF middleware and tokens on mutating forms.
- Login/staff decorators and owner-scoped booking queries.
- Server-derived booking price/reference/room/user/status.
- Form/model validators for dates, capacity, positive values, email, and username.
- Production secret requirement, HTTPS redirect, secure cookies, and HSTS.
- Escaped Django template output for user-controlled text.
- Minimal username JSON response and basic session throttling.

No formal penetration test, Content Security Policy, production rate-limiting service, or audit logging is implemented.

## 11. Testing methodology and results

On 2026-10-20, the latest full suite reported 42/42 passing in 5.935 seconds. Django checks reported zero issues, migrations had no drift, and pip reported no broken requirements. Manual browser checks covered major desktop/mobile customer and staff surfaces, signup steps, username feedback, notification placement/dismissal, and console errors. See `TESTING.md` for commands and gaps.

## 12. Dependencies

- Django 4.2.30: web framework, ORM, forms, auth, messages, templates, and admin.
- Pillow 11.3.0: validates and processes `ImageField` uploads.

No new notification, SPA, or JavaScript framework was added. Bootstrap, Bootstrap Icons, Google Fonts, and Chart.js are CDN assets rather than Python dependencies.

## 13. Files grouped by feature

- Configuration: `staywise/settings.py`, `staywise/urls.py`, `.env.example`, `.gitignore`, `requirements.txt`.
- Accounts/dashboards: `accounts/forms.py`, `accounts/views.py`, `accounts/services.py`, `accounts/urls.py`, account templates, `dashboard_base.html`.
- Rooms: `hotels/models.py`, `hotels/forms.py`, `hotels/views.py`, hotel templates, admin, migrations, `seed_demo.py`.
- Bookings: `bookings/models.py`, `bookings/forms.py`, `bookings/views.py`, booking templates, admin, migrations.
- Recommendations: model/form/view/service, templates, migrations, evaluator command.
- Design: `templates/base.html`, `templates/includes/*`, `static/css/site.css`, `toasts.css`, `admin.css`, `static/js/site.js`, local images.
- Verification: the four `tests.py` modules.
- Documentation: `README.md` and `docs/*`.

## 14. Manually verified workflows

Homepage/search, room list/detail, signup steps, live username status, login, preference form and redirect toast, recommendations, customer dashboard/sidebar, mobile layouts, staff dashboard/charts, Django Admin, image fallbacks, and toast dismissal/positioning were inspected. Browser console checks returned no warnings or errors during the final UI verification.

## 15. Remaining defects, limitations, and risks

- SQLite cannot provide effective row locking for booking concurrency.
- Python 3.9 and Django 4.2 are out of upstream support as of the current date; upgrade testing is needed.
- External CDN availability affects styling/icons/fonts/charts.
- The demo rooms reuse one room image; additional owned photography would improve realism.
- The development database contains local QA/demo records and is intentionally ignored by Git.
- No measured code coverage, JS unit tests, accessibility automation, load tests, or production SMTP/storage tests.
- Session throttling is per session and is not a distributed abuse-control mechanism.

## 16. Deployment considerations

Use Python 3.12+ and Django 5.2 LTS after regression testing, PostgreSQL, a production WSGI/ASGI server, reverse-proxy TLS, persistent media/object storage, SMTP, monitoring, backups, and environment-managed secrets. Run `check --deploy`, migrations, tests, and `collectstatic`; configure allowed hosts and secure proxy headers where applicable. Do not deploy the included SQLite database as production storage.

## 17. Future improvements

Add PostgreSQL interval constraints, payment lifecycle if required, email delivery tests, local vendoring/build pipeline for frontend assets, labelled recommendation evaluation, richer room photography, accessibility/visual regression automation, CI, audit logging, and production observability.

## 18. Setup and demonstration

Follow `README.md` for installation. For a demonstration: seed rooms, create a superuser, register a guest, save preferences, explain a recommendation score, book a future room, show history/cancellation, then sign in as staff to explain period availability, revenue definition, trends, filters, and admin inventory management.
