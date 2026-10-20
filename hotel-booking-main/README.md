# Staywise — Hotel Booking and Explainable Recommendation System

Staywise is a Django final-year project for room discovery, authenticated booking,
customer and staff dashboards, and deterministic weighted content-based recommendations.
The recommender is rule-based and explainable; it is not a trained machine-learning model.

## Objectives, features, and roles

Staywise demonstrates a maintainable hotel-booking workflow in which important rules are
enforced by Django rather than trusted to the browser. Public visitors can browse and
filter active rooms. Registered customers can maintain preferences, receive scored and
explained recommendations, book available rooms, review their history, edit their profile,
and cancel eligible future stays. Staff can view database-backed operational metrics and
use protected Django Admin inventory, booking, and customer management.

## Technology and dependencies

- Python and Django
- SQLite for local development
- Django templates, HTML, CSS, and vanilla JavaScript
- Bootstrap 5 and Bootstrap Icons
- Chart.js for database-backed staff trends
- Pillow for uploaded room images

The application is a server-rendered Django monolith split into four apps. Views coordinate
forms and services, Django's ORM stores data, templates render HTML, and vanilla JavaScript
adds progressive enhancements such as the signup wizard, toast lifecycle, and mobile
dashboard navigation. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Repository structure

```text
accounts/          authentication, profiles, dashboards, staff metrics
hotels/            hotel/room/amenity inventory and public discovery
bookings/          booking rules, forms, ownership, history, cancellation
recommendations/   preferences, weighted scoring, explanations, evaluation
staywise/          project settings, root URLs, WSGI entry point
templates/         base layouts, page templates, and reusable partials
static/            Mint & Seafoam CSS, JavaScript, and local images
docs/              architecture, algorithm, testing, changelog, final report
```

Pinned Python packages are in `requirements.txt`. This checkout currently uses Django
4.2.30 and Pillow 11.3.0. Django 4.2 and Python 3.9 are no longer upstream-supported;
plan a tested migration to Python 3.12+ and Django 5.2 LTS before production use.

## Local setup

Prerequisites are Python and pip. The inspected environment uses Python 3.9.6, but Python
3.12+ is recommended together with a tested Django 5.2 LTS upgrade for future deployment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Staff can use `/accounts/staff/` and Django Admin at
`/admin/`. `seed_demo` is idempotent and creates demonstration hotels, rooms, and
amenities without deleting existing data.

`migrate` creates missing tables without intentionally deleting populated records. Back up
important databases before migrations. `seed_demo` uses `get_or_create` and is safe to run
again, but it is development/demo data rather than production content.

## Main routes

| Route | Purpose | Access |
| --- | --- | --- |
| `/` | Homepage and date/guest search entry | Public |
| `/rooms/` | Room filters and paginated results | Public |
| `/rooms/<id>/` | Active room detail | Public |
| `/accounts/signup/` | Three-step registration presentation | Guest |
| `/accounts/login/` | Login | Guest |
| `/accounts/password_reset/` | Password reset request | Public |
| `/accounts/dashboard/` | Customer bookings, metrics, and recommendations | Login required |
| `/recommendations/preferences/` | Saved matching preferences | Login required |
| `/recommendations/` | Ranked explainable matches | Login required |
| `/bookings/` | Owned booking history | Login required |
| `/accounts/staff/` | Operational dashboard | Staff required |
| `/admin/` | Inventory/customer/booking administration | Staff plus model permissions |

## Configuration and secrets

Configuration uses environment variables:

- `DJANGO_DEBUG`: defaults to `True` locally; set `False` in production.
- `DJANGO_SECRET_KEY`: required when debug is false. Never commit a real value.
- `DJANGO_ALLOWED_HOSTS`: comma-separated hosts.
- `DJANGO_EMAIL_BACKEND`: optional email backend override; development defaults to Django's console backend.

`.env.example` documents the names, but this project deliberately does not parse `.env`
files or require an extra package. Export variables through the shell or deployment
platform. When no local secret is supplied in debug mode, a temporary random key is
created at startup; sessions are therefore invalidated after a development-server restart.

Production example:

```bash
export DJANGO_DEBUG=False
export DJANGO_SECRET_KEY='generate-a-long-random-value'
export DJANGO_ALLOWED_HOSTS='hotel.example.com'
python manage.py check --deploy
python manage.py collectstatic --noinput
```

SQLite data (`db.sqlite3`), uploads (`media/`), virtual environments, and `.env` are
excluded from version control.

## Database and migrations

```bash
python manage.py showmigrations
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

Do not delete or recreate a populated production database. Back up data before migrations.
SQLite is appropriate for demonstration and development, but does not provide effective
row-level locking for Django's `select_for_update()`. The submission transaction and
second availability check reduce the race window; a concurrent production deployment
should use PostgreSQL while retaining the same transaction and room lock.

## Authentication and permissions

- Registration uses Django password validation and case-insensitive unique email checks.
- Registration is presented as an accessible three-step flow while one Django form remains the server-side source of truth. Its CSRF-protected, session-throttled username check returns validation state only; final uniqueness validation remains server-side.
- Login and logout use Django authentication; logout and cancellation are POST-only.
- Every mutating HTML form has CSRF protection.
- Booking history, detail, and cancellation queries are restricted to the current owner.
- Customer profile updates expose only first name, last name, and email.
- Staff dashboards require an active staff account; management operations remain behind
  Django Admin permissions.
- Booking price, room, owner, status, and reference are never accepted from customer forms.

## Booking rules

The server requires a future-or-current check-in, check-out after check-in, at least one
guest, sufficient room capacity, and an available room status. Total price is calculated
from the stored nightly rate and number of nights at creation and retained as a historical
snapshot if room pricing later changes.

Confirmed stays overlap when:

`existing.check_in < requested.check_out AND existing.check_out > requested.check_in`

Cancelled and pending records do not block dates. Adjacent stays are allowed. Availability
is checked during search and again inside the booking transaction. Customers may cancel
their own pending or confirmed reservation only before its check-in date.

## Explainable recommendation formula

Hard constraints run before ranking: room status must be available, capacity must satisfy
the party size, and no confirmed booking may overlap requested dates.

Each eligible room receives normalized feature scores in `[0, 1]`:

- budget: 1 at or below the maximum, declining linearly to 0 at 150% of budget;
- destination: exact case-insensitive city/country match, or neutral 0.5 if unspecified;
- room type: exact categorical match, or neutral 0.5 if unspecified;
- amenities: selected amenities matched divided by selected amenities, or neutral 0.5;
- capacity: `min(room capacity / guests, 1)` after the hard capacity check.

Configured weights in `staywise/settings.py` are budget 30%, destination 20%, room type
20%, amenities 20%, and capacity 10%. They are normalized automatically:

`score = 100 × Σ(normalized feature score × normalized configured weight)`

Results sort by descending score, lower nightly price, then room ID. Cards expose each raw
feature score, weight, point contribution, and human-readable reasons. Missing optional
preferences receive neutral scores. Run the small offline evaluation with:

```bash
python manage.py evaluate_recommender
```

The report measures result coverage, not predictive accuracy. Limitations include equal
amenity importance, exact categorical matching, no collaborative behavior, no learned
feedback, and a soft rather than hard budget limit. Future work can add labelled relevance
judgements, diversity metrics, amenity importance, feedback loops, PostgreSQL range
constraints, and a separately evaluated trained ranker if suitable data becomes available.

## Staff metric definitions

Staff select an inclusive check-in period. Booking counts and cancellations include stays
whose check-in falls in that period. Revenue sums confirmed and completed booking totals;
it is booked revenue, not proof of payment collection. Period availability is the count of
active rooms without a confirmed booking overlapping any part of the selected interval.

## Tests and quality checks

```bash
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
python -m pip check
```

Tests cover authentication, staff permissions, CSRF, booking ownership, server-calculated
prices, historical price retention, invalid dates and capacity, overlaps, adjacent dates,
cancelled bookings, filters, dashboards, metrics, recommendation scoring, availability,
ties, missing preferences, and empty datasets.

The latest observed run on 2026-10-20 passed 42 tests. This is not a measured coverage
percentage. Exact results, manual checks, and known test gaps are recorded in
[`docs/TESTING.md`](docs/TESTING.md).

## Main workflow summary

- **Registration:** one `SignUpForm` is visually divided into three JavaScript steps. Only
  the final button submits. Django remains responsible for username/password/email
  validation and repopulates values after errors.
- **Username checking:** a debounced CSRF-protected POST reuses Django's username field
  rules and returns only validation state. Database uniqueness during final signup is
  authoritative.
- **Messages:** Django messages render once in a shared partial. The idempotent vanilla
  manager stacks, dismisses, and removes fixed toasts without changing page layout.
- **Search:** a Django form validates dates, guests, prices, and amenities; confirmed
  overlapping bookings are excluded only for the requested interval.
- **Booking:** the view accepts only safe form fields, assigns the current user/room, locks
  within a transaction where supported, then model validation rechecks capacity and
  overlap and derives the total.
- **Recommendations:** hard constraints run first; five normalized feature scores are
  weighted, explained, and deterministically sorted. See
  [`docs/RECOMMENDATION_ENGINE.md`](docs/RECOMMENDATION_ENGINE.md).

## Troubleshooting

- **`ModuleNotFoundError: django`:** activate `.venv` and install `requirements.txt`.
- **Pending migrations:** run `python manage.py showmigrations` and `python manage.py migrate`.
- **No rooms shown:** run `python manage.py seed_demo`, then check room status in Admin.
- **Images do not upload:** confirm Pillow is installed and `media/` is writable locally.
- **Password reset email does not arrive:** development prints it to the runserver console;
  configure `DJANGO_EMAIL_BACKEND` and SMTP settings for deployment.
- **Styles/charts missing offline:** Bootstrap, icons, fonts, and Chart.js are currently
  loaded from CDNs. Database workflows still run, and charts display a fallback message.
- **Sessions reset after server restart:** provide a stable local `DJANGO_SECRET_KEY`;
  otherwise debug mode intentionally generates a temporary key.

## Current limitations and future work

SQLite is not sufficient for strong concurrent booking locks. Production work should move
to PostgreSQL and consider a database interval exclusion constraint. Other priorities are
Python/Django LTS upgrades, production SMTP/media storage, CI, accessibility and visual
regression automation, measured code coverage, load testing, and relevance-labelled
recommendation evaluation. See [`docs/IMPLEMENTATION_REPORT.md`](docs/IMPLEMENTATION_REPORT.md)
for status distinctions and deployment considerations.

## Documentation index

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/RECOMMENDATION_ENGINE.md`](docs/RECOMMENDATION_ENGINE.md)
- [`docs/TESTING.md`](docs/TESTING.md)
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md)
- [`docs/IMPLEMENTATION_REPORT.md`](docs/IMPLEMENTATION_REPORT.md)
