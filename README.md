# Staywise Hotel Booking & AI Recommendation Platform

A Django hotel booking application featuring an intelligent **Hybrid AI Recommendation Engine** (TF-IDF semantic similarity, multi-criteria scoring) and an interactive **AI Travel Concierge** (natural language search, personalized explanations, and automatic offline fallback).

## Quick Start

```bash
cd hotel-booking-main
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open `http://127.0.0.1:8000/recommendations/` to explore the AI Concierge and room recommendations.
