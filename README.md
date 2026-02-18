<div align="center">

# 💈 BarberSync

### Privacy-First Appointment Booking for Modern Barbershops

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

**📅 Zero-Friction Booking** • **🔒 Zero PII Storage** • **⚡ 60-Second Experience**

[Documentation](ARCHITECTURE.md)

---

</div>

## Tech Stack (Planned)
- **Backend:** Python 3.12 / Django 6.0
- **Database:** PostgreSQL (via Supabase)
- **Architecture:** Monolithic API with Managed Cloud Database
- **Frontend:** Responsive Web (Mobile-First)

## Core Logic Requirements
- **Zero PII Policy:** No user accounts or personal data stored. Appointments are tracked via Unique Ref IDs.
- **5-Minute Soft Hold:** Slots are temporarily locked during the checkout process to prevent double-booking.
- **24-Hour Barber Review:** Barbers have a 24-hour window to accept/decline pending requests before the slot is auto-released.
- **3-Week Rolling Window:** Availability is dynamically calculated to show only the next 21 days.

## Getting Started
1. Clone the repo: `git clone [REPO_URL]`
2. Create a `.env` file with `DATABASE_URL` and `SECRET_KEY`.
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
