# BarberSync 
Digitalizing appointment booking for a barbershop with a focus on zero-friction and privacy..

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