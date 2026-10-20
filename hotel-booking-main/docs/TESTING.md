# Testing and Verification

## Automated suites

Django discovers 42 tests across four applications:

| Suite | Coverage represented by current tests |
| --- | --- |
| `accounts.tests` | Auth-page rendering, registration/login/logout, duplicate email, username endpoint, all message levels, inline errors, customer ownership, profile editing, staff permissions, metrics, filters, and empty datasets. |
| `hotels.tests` | Public pages, invalid/past dates, inactive-room visibility, price/guest/amenity filters, and confirmed versus cancelled availability. |
| `bookings.tests` | Server price, price snapshot, overlap, adjacency, cancelled availability, dates, capacity, zero guests, authentication, ownership, POST-only cancellation, and CSRF rejection. |
| `recommendations.tests` | Perfect score and explanation, weight normalization, budget normalization, capacity/date hard constraints, cancelled bookings, missing preferences, deterministic ties, coverage reporting, and protected pages. |

## Commands and observed results

Executed on 2026-10-20 with Python 3.9.6 and Django 4.2.30:

```bash
.venv/bin/python manage.py test
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python -m pip check
```

Observed results:

- 42 tests found; 42 passed in 5.935 seconds.
- Django system check: 0 issues.
- Migration drift: no changes detected.
- Dependency consistency: no broken requirements.

The duration is a single local run, not a performance benchmark.

Additional diagnostic commands:

```bash
python manage.py showmigrations --plan
python manage.py evaluate_recommender
```

All project and Django migrations were applied in the inspected development database. The evaluator's current result is documented in `RECOMMENDATION_ENGINE.md`.

## Security and permission checks

Automated tests verify login requirements, staff-only dashboard access, owner-filtered booking detail/cancellation, POST-only cancellation, CSRF rejection, non-client-controlled total price, inactive inventory exclusion, and minimal username-check responses. Production security settings can be inspected with:

```bash
DJANGO_DEBUG=False DJANGO_SECRET_KEY='temporary-check-only-secret' \
DJANGO_ALLOWED_HOSTS='example.com' python manage.py check --deploy
```

Use a non-production temporary value for this diagnostic; never commit or print a real secret.

## Manual browser verification

### Authentication

1. Visit `/accounts/signup/` and move through all three visual steps.
2. Enter a username of at least three characters; confirm loading and available/taken feedback.
3. Submit mismatched passwords and verify inline feedback; submit valid details and confirm redirect to preferences.
4. Sign out using the POST action and sign in again.
5. Use “Forgot password?”; in development, read the reset link from the server console because the default backend is console email.

### Rooms and bookings

1. Visit `/rooms/`; test destination, guests, price, amenities, and paired dates.
2. Confirm invalid and past dates display beside the relevant field.
3. Open a room, submit a valid booking, and compare nights × displayed nightly price with the confirmation total.
4. Try the same confirmed interval from another account and verify rejection.
5. Verify a stay beginning on the previous stay's check-out date is allowed.
6. Open `/bookings/`, inspect owned details, and cancel a future booking. Confirm cancelled dates become searchable again.

### Recommendations and dashboards

1. Save preferences at `/recommendations/preferences/` and confirm a success toast after redirect.
2. Inspect match percentages, reasons, and score breakdowns.
3. Confirm requested dates and guest capacity remove ineligible rooms.
4. Visit `/accounts/dashboard/` on desktop and mobile; verify metrics, empty states, sidebar, trips, and recommendations.
5. With a staff account, visit `/accounts/staff/`; change dates, search/filter bookings, and compare figures with Django Admin records.

### Toasts and responsiveness

1. Trigger success messages through registration, preference saving, profile editing, booking, or cancellation.
2. Trigger booking cancellation error/info paths where applicable.
3. At desktop width, confirm the toast is below navigation at top-right and does not reflow content.
4. At approximately 390px width, confirm 12px side margins and no overlap with the mobile header.
5. Test manual dismissal and keyboard focus. Enable reduced motion in the operating system and confirm animations are removed.

## Browser checks already observed

Desktop and 390×844 mobile layouts were inspected for signup, preferences, recommendations, customer dashboard, mobile sidebar, rooms, room detail, staff dashboard, admin, and notification positioning. Signup was additionally measured at 1440×800 and 390×844: document height equalled viewport height and the Continue action remained visible. The most recent toast check measured 90px desktop top/16px right and 78px mobile top/12px sides. No browser console errors or warnings were observed in those checks.

## Known testing gaps

- No measured statement/branch coverage percentage exists.
- JavaScript has browser smoke checks but no dedicated unit-test runner.
- No automated accessibility scanner, visual-regression baseline, load test, or multi-process concurrency test exists.
- Password email delivery is not tested against a production SMTP provider.
- SQLite cannot validate the intended production row-lock behavior.
- Chart.js CDN failure has a UI fallback but is not tested by an automated browser network simulation.
