# Staywise — Room Booking & Recommendation System for TR5 (Ruyenzi, Rwanda)

A web-based room booking and recommendation platform built for **TR5 in Ruyenzi, Rwanda**, and adaptable for small and medium hotels across **Kigali**.

## Features (Chapters One to Four)

- **Customer Side**: Registration & hashed authentication, room catalog with photos and features, filters by dates, room type, and price, saved preferences (price, bed type, view, breakfast, AC, quietness), top 3 recommended rooms scoring $\ge 80\%$, transactional booking safety (no double-booking), and booking history.
- **Administrator Side**: Full Django Admin for rooms, features, images, and prices; staff operations dashboard with Chart.js trend charts.
- **Recommendation Engine**: Content-based filtering with hand-calibrated weights summing to 1.0, plus an optional Hybrid AI Concierge.
- **Database & Safety**: SQLite with `select_for_update` transactional isolation preventing duplicate bookings.

## Quick Start

```bash
cd hotel-booking-main
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

- Public rooms: `http://127.0.0.1:8000/rooms/`
- Top recommendations: `http://127.0.0.1:8000/recommendations/`
- Operations dashboard: `http://127.0.0.1:8000/accounts/staff/`
- Default test users: seeded with passwords (`Guest@12345`)

## Access from your phone (same Wi-Fi)

`runserver` binds to `127.0.0.1` by default, so a phone cannot reach it. Start it on
all interfaces instead:

```powershell
cd hotel-booking-main
.\run_lan.ps1
```

The script applies pending migrations, prints both URLs, and detects the Wi-Fi IP.
The manual equivalent is:

```powershell
python manage.py runserver 0.0.0.0:8000
ipconfig   # find the Wi-Fi IPv4 address, e.g. 10.25.1.176
```

Then open `http://<wifi-ipv4>:8000/` on the phone. While `DEBUG=True` the app accepts
any host, so the LAN address works out of the box; production deployments must set an
explicit `DJANGO_ALLOWED_HOSTS` list.

If the phone still cannot connect, allow the port through Windows Defender Firewall
once from an **Administrator** PowerShell, or run `.\run_lan.ps1 -OpenFirewall`:

```powershell
New-NetFirewallRule -DisplayName "Staywise Django 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private,Public
```

Campus/guest Wi-Fi networks often isolate clients from each other. If that happens,
connect the computer to the phone's mobile hotspot and use the new Wi-Fi IP shown by
`ipconfig`.
