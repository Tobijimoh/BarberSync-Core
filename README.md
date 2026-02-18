# 💈 BarberSync

**A privacy-first booking system for modern barbershops**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

> Streamline your barbershop's appointment management with zero friction and maximum privacy.

---

## Overview

BarberSync is a lightweight, privacy-focused booking platform designed specifically for small barbershops. Book appointments in under 60 seconds—no accounts, no personal data, no hassle.

### Key Features

- **Zero PII Storage** — No names, emails, or phone numbers collected
- **60-Second Booking** — Quick, frictionless customer experience
- **Database-Level Integrity** — Double-booking prevention at the PostgreSQL level
- **Mobile-First** — Optimized for on-the-go booking
- **GDPR Compliant by Design** — Privacy built into the architecture

---

## Architecture

```
┌─────────────┐
│   Customer  │
│   Frontend  │
└──────┬──────┘
       │ HTTPS/REST
       ▼
┌─────────────────┐
│  Django REST    │
│   Framework     │
├─────────────────┤
│ Business Logic: │
│ • Slot Gen      │
│ • Validation    │
│ • State Mgmt    │
└──────┬──────────┘
       │ Django ORM
       ▼
┌─────────────────┐
│   PostgreSQL    │
│   (Supabase)    │
└─────────────────┘
```

---

## Privacy-First Design

### How BarberSync Protects Customer Privacy:

| Traditional Systems | BarberSync |
|---------------------|------------|
| ❌ Email required | ✅ No email |
| ❌ Phone number stored | ✅ No phone |
| ❌ Account creation | ✅ No accounts |
| ❌ Password management | ✅ Reference-only system |

**Appointments are tracked via unique reference codes** (e.g., `BS-183947`) — that's it.

---

## ⚙️ Core Business Logic

### Booking Flow

```
Customer selects slot
       ↓
SOFT_HOLD (5 min timer)
       ↓
Customer confirms
       ↓
PENDING (24h barber review)
       ↓
Barber accepts/declines
       ↓
CONFIRMED or CANCELLED
```

### Key Timers

- **5-Minute Soft Hold** — Slots locked during checkout to prevent race conditions
- **24-Hour Barber Window** — Reasonable time to review and respond to requests
- **21-Day Rolling Window** — Only show next 3 weeks to prevent calendar bloat

### Double-Booking Prevention

BarberSync uses a **partial unique index** at the database level:

```sql
CREATE UNIQUE INDEX unique_active_slot 
ON appointments (barber_id, slot_datetime) 
WHERE status IN ('SOFT_HOLD', 'PENDING', 'CONFIRMED');
```

This means the database **physically prevents** two people from booking the same slot—even if there's a bug in the application code.

---

## Tech Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| **Backend** | Python 3.12 + Django 5.0 | Built-in admin panel, robust ORM |
| **API** | Django REST Framework | Industry-standard, well-documented |
| **Database** | PostgreSQL 15+ | Datetime handling, partial indexes |
| **Hosting** | Render (Backend) + Supabase (DB) | Free tiers, easy deployment |
| **Frontend** | React (planned) | Mobile-first, responsive |

---

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/barbersync.git
   cd barbersync
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser** (for admin access)
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/

---

## API Documentation

### Core Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/barbers/` | List active barbers | No |
| `GET` | `/api/availability/` | Get available time slots | No |
| `POST` | `/api/appointments/` | Create booking (soft hold) | No |
| `PATCH` | `/api/appointments/{ref}/confirm/` | Confirm booking | No |
| `GET` | `/api/appointments/{ref}/` | Check status | No |
| `DELETE` | `/api/appointments/{ref}/` | Cancel booking | No |
| `PATCH` | `/api/appointments/{ref}/accept/` | Barber accepts | Yes |
| `PATCH` | `/api/appointments/{ref}/decline/` | Barber declines | Yes |

### Example Request

**Create a booking:**
```bash
curl -X POST http://localhost:8000/api/appointments/ \
  -H "Content-Type: application/json" \
  -d '{
    "barber_id": "550e8400-e29b-41d4-a716-446655440000",
    "slot_datetime": "2026-02-20T14:00:00Z"
  }'
```

**Response:**
```json
{
  "appointment_ref": "BS-183947",
  "barber": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "display_name": "Barber A"
  },
  "slot_datetime": "2026-02-20T14:00:00Z",
  "status": "SOFT_HOLD",
  "expires_at": "2026-02-20T14:05:00Z"
}
```


---

## Running Tests

```bash
# Run all tests
python manage.py test

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

---

## Deployment

### Deploy to Render (Backend)

1. Push code to GitHub
2. Connect Render to your repository
3. Set environment variables in Render dashboard
4. Deploy!

### Database (Supabase)

1. Create project on Supabase
2. Copy database URL
3. Add to `.env` as `DATABASE_URL`
4. Run migrations

---

<div align="center">

**[Documentation](ARCHITECTURE.md)**

</div>
