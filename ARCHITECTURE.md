# BarberSync - Technical Architecture & System Design

**Version:** 1.0  
**Last Updated:** February 2026  


---

## 1. Executive Summary

BarberSync is a specialized booking engine designed for a two-barber shop environment. The system is engineered for **Zero-Friction Booking**, requiring no user accounts or stored PII (Personally Identifiable Information), while enforcing strict database-level constraints to ensure 100% schedule integrity.

**Key Design Principles:**
- **Privacy First:** No customer PII stored (GDPR compliant by design)
- **Database-Level Integrity:** Double-booking prevention enforced at PostgreSQL level
- **Stateless Client:** All state managed server-side via appointment references
- **Fail-Safe Scheduling:** Soft-hold mechanism prevents booking conflicts

---

## 2. System Overview

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────┐              ┌──────────────────┐    │
│  │  Customer Web    │              │  Barber Admin    │    │
│  │  Interface       │              │  Dashboard       │    │
│  │  (React/HTML)    │              │  (Django Admin)  │    │
│  └────────┬─────────┘              └─────────┬────────┘    │
│           │                                   │            │
└───────────┼───────────────────────────────────┼────────────┘
            │                                   │
            │         HTTPS/REST API            │
            │                                   │
┌───────────▼───────────────────────────────────▼────────────┐
│                   APPLICATION LAYER                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Django REST Framework (DRF)                │    │
│  │                                                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │    │
│  │  │  Booking     │  │  Availability│  │  Status  │  │    │
│  │  │  ViewSet     │  │  ViewSet     │  │  ViewSet │  │    │
│  │  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  │    │
│  └─────────┼─────────────────┼───────────────┼────────┘    │
│            │                  │               │            │
│  ┌─────────▼──────────────────▼───────────────▼───────┐    │
│  │            Business Logic Layer                    │    │
│  │  - Slot generation                                 │    │
│  │  - Reference generation                            │    │
│  │  - Booking validation                              │    │
│  │  - State transitions (SOFT_HOLD → PENDING → ...)   │    │
│  └──────────────────────────┬─────────────────────────┘    │
│                             │                              │
└─────────────────────────────┼──────────────────────────────┘
                              │
                  Django ORM (psycopg2)
                              │
┌─────────────────────────────▼────────────────────────────┐
│                    DATA LAYER                            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│              PostgreSQL Database (Supabase)              │
│                                                          │
│  ┌──────────┐  ┌─────────────┐  ┌───────────────┐        │
│  │ barbers  │  │appointments │  │system_settings│        │
│  └──────────┘  └─────────────┘  └───────────────┘        │
│                                                          │
│  Constraints: Unique Index on (barber_id, slot_datetime) │
│              WHERE status IN ('SOFT_HOLD', 'PENDING',    │
│                               'CONFIRMED')               │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

### Backend
- **Language:** Python 3.12
- **Framework:** Django 6.0
- **API Layer:** Django REST Framework (DRF) 3.15
- **Database ORM:** Django ORM (psycopg2-binary)
- **Task Queue:** Django management commands (for cleanup tasks)

### Database
- **Database:** PostgreSQL 15+
- **Hosting:** Supabase (managed PostgreSQL with SSL)
- **Key Features Used:**
  - Partial unique indexes
  - Timestamp with timezone support
  - Foreign key constraints

### Infrastructure
- **Architecture Pattern:** Monolithic backend with RESTful API
- **Deployment:** Render.com (Python web service)
- **Environment Management:** python-dotenv for configuration
- **Version Control:** Git + GitHub

### Why This Stack?

| Decision | Rationale |
|----------|-----------|
| **Django** | Built-in admin panel perfect for barber dashboard; robust ORM; excellent documentation |
| **PostgreSQL** | Strong datetime handling; partial indexes support; ACID compliance critical for booking integrity |
| **Monolith** | Small scale (2 barbers); simpler deployment; no need for microservices complexity |
| **Supabase** | Free tier sufficient; managed backups; SSL built-in; good monitoring tools |

---

## 4. Database Schema Design

### Entity Relationship Diagram

```
┌─────────────────────┐
│     barbers         │
├─────────────────────┤
│ id (PK)             │──┐
│ display_name (Char) │  │
│ email_address (Char)│  │
| login_password(Char)|  │
│ is_active (Bol)     │  │
│ created_at          │  │
└─────────────────────┘  │
                         │ 1
                         │
                         │ Many
                         │
                         │
┌─────────────────────────────────┐
│        appointments             │
├─────────────────────────────────┤
│ id (PK)                         │
│ appointment_ref (Unique)        │
│ barber_id (FK) ─────────────────┘
│ slot_datetime                   │
│ status (Enum)                   │
│ source (Enum)                   │
│ created_at                      │
│ updated_at                      │
└─────────────────────────────────┘
         
         
        
┌─────────────────────────────┐
│  system_settings            │
├─────────────────────────────┤
│ id (PK)                     │
│ opening_hour (TIME)         │
│ closing_hour (TIME)         │
│ slot_duration_minutes (INT) │
│ booking_window_days (INT)   │
│ hold_expiry_minutes (INT)   │
│ barber_accept_hours (INT)   │
│ updated_at (TIMESTAMP)      │
└─────────────────────────────┘
```
**Relationship Type:** One-to-Many
- One barber can have many appointments
- Each appointment belongs to exactly one barber
- System settings is a standalone configuration table (no foreign key relationships)

### Table: `barbers`

Stores professional profiles available for booking.

```sql
CREATE TABLE barbers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Django Model:**
```python
class Barber(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### Table: `appointments`

The central ledger for all scheduling activity.

```sql
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_ref VARCHAR(20) UNIQUE NOT NULL,
    barber_id UUID NOT NULL REFERENCES barbers(id) ON DELETE RESTRICT,
    slot_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN (
        'SOFT_HOLD', 'PENDING', 'CONFIRMED', 'CANCELLED', 'EXPIRED', 'BLOCKED'
    )),
    source VARCHAR(20) NOT NULL DEFAULT 'WEB' CHECK (source IN ('WEB', 'ADMIN_MANUAL')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Critical: Prevent double-booking at database level
CREATE UNIQUE INDEX unique_active_slot 
ON appointments (barber_id, slot_datetime) 
WHERE status IN ('SOFT_HOLD', 'PENDING', 'CONFIRMED');
```

**Django Model:**
```python
class AppointmentStatus(models.TextChoices):
    SOFT_HOLD = 'SOFT_HOLD', 'Soft Hold'
    PENDING = 'PENDING', 'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    EXPIRED = 'EXPIRED', 'Expired'
    BLOCKED = 'BLOCKED', 'Blocked'

class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment_ref = models.CharField(max_length=20, unique=True)
    barber = models.ForeignKey('Barber', on_delete=models.RESTRICT, related_name='appointments')
    slot_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=AppointmentStatus.choices)
    source = models.CharField(max_length=20, default='WEB')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['barber', 'slot_datetime'],
                condition=models.Q(status__in=['SOFT_HOLD', 'PENDING', 'CONFIRMED']),
                name='unique_active_slot'
            )
        ]
```

**Status State Machine:**
```
┌─────────────┐
│  SOFT_HOLD  │ ←── Customer selects slot (5 min timer starts)
└──────┬──────┘
       │
       │ Customer confirms OR Timer expires
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌─────────────┐  ┌───────────┐
│   PENDING   │  │ (deleted) │ ←── Soft hold expired
└──────┬──────┘  └───────────┘
       │
       │ Barber responds within 24h
       │
       ├──────────────────┬──────────────┐
       │                  │              │
       ▼                  ▼              ▼
┌─────────────┐  ┌──────────────┐  ┌──────────┐
│  CONFIRMED  │  │  CANCELLED   │  │  EXPIRED │
└─────────────┘  └──────────────┘  └──────────┘
```

---

### Table: `system_settings`

Global configuration for business logic parameters.

```sql
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(50) UNIQUE NOT NULL,
    setting_value VARCHAR(100) NOT NULL,
    description TEXT
);

-- Initial data
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('opening_hour', '08:00', 'Shop opening time (24h format)'),
('closing_hour', '20:00', 'Shop closing time (24h format)'),
('slot_duration_minutes', '60', 'Length of each appointment'),
('booking_window_days', '21', 'Maximum days customers can book ahead'),
('hold_expiry_minutes', '5', 'Soft hold timeout for customer checkout'),
('barber_accept_hours', '24', 'Hours barber has to accept booking');
```

---

## 5. Core Business Logic

### 5.1 Appointment Booking Flow

```
Customer Journey:
─────────────────

1. Customer visits booking page
   ↓
2. Selects barber from dropdown
   ↓
3. Views available slots (API: GET /api/availability/)
   ↓
4. Clicks on desired slot
   ↓
5. System creates SOFT_HOLD record (API: POST /api/appointments/)
   ↓ (Timer: 5 minutes)
6. Customer confirms details
   ↓
7. Status changes to PENDING (API: PATCH /api/appointments/{ref}/confirm)
   ↓
8. Customer receives appointment_ref (e.g., "BS-183947")
   ↓ (Timer: 24 hours)

Barber Journey:
───────────────

9. Barber sees notification in admin panel
   ↓
10. Barber reviews appointment details
    ↓
11. Barber clicks "Accept" or "Decline"
    ↓
    ├─ Accept → Status: CONFIRMED
    │
    └─ Decline → Status: CANCELLED (slot released)
```

---

### 5.2 Soft Hold Mechanism (5-Minute Browser Timeout)

**Purpose:** Prevent race conditions where multiple users attempt to book the same slot simultaneously.

**Implementation:**

1. **Initiation:**
   - User clicks slot → `POST /api/appointments/` with `{barber_id, slot_datetime}`
   - Backend creates record with `status = SOFT_HOLD`
   - Database unique constraint ensures no other user can hold this slot

2. **Client-Side Timer:**
   - Frontend displays countdown: "You have 4:52 remaining to confirm"
   - If timer expires before confirmation, frontend shows "Slot expired, please try again"

3. **Backend Cleanup:**
   - Scheduled task runs every 2 minutes: `python manage.py cleanup_expired_holds`
   - Deletes records where `status = SOFT_HOLD` AND `created_at < NOW() - 5 minutes`

**Edge Case Handling:**
- If user confirms after 5 minutes → Backend rejects (slot may already be taken)
- If user closes browser → Automatic cleanup releases slot within 5 minutes

---

### 5.3 Barber Acceptance Window (24-Hour Window)

**Purpose:** Give barbers reasonable time to review and respond to booking requests.

**Implementation:**

1. **State Transition:**
   - When customer confirms → status changes from `SOFT_HOLD` to `PENDING`
   - `updated_at` timestamp is recorded

2. **Barber Notification:**
   - Django admin shows badge count of pending requests
   - Future: Push notification or SMS to barber's phone

3. **Expiry Logic:**
   - Scheduled task runs hourly: `python manage.py expire_pending_appointments`
   - Finds records where `status = PENDING` AND `updated_at < NOW() - 24 hours`
   - Updates `status = EXPIRED`

4. **Slot Release:**
   - Expired appointments become available again (unique constraint no longer applies)
   - Customer can check status via `GET /api/appointments/{ref}/` and see `EXPIRED`

---

### 5.4 Rolling 3-Week Availability Window

**Purpose:** Prevent long-term calendar bloat and reduce no-shows.

**Implementation:**

```python
from datetime import datetime, timedelta
from django.utils import timezone

def get_booking_window():
    """Calculate valid booking date range"""
    today = timezone.now().date()
    max_date = today + timedelta(days=21)
    return today, max_date

def validate_slot_datetime(slot_datetime):
    """Ensure slot is within booking window"""
    today, max_date = get_booking_window()
    slot_date = slot_datetime.date()
    
    if slot_date < today:
        raise ValidationError("Cannot book slots in the past")
    
    if slot_date > max_date:
        raise ValidationError(f"Cannot book more than 21 days ahead (max: {max_date})")
    
    return True
```

**API Response:**
```json
{
  "available_dates": {
    "start": "2026-02-17",
    "end": "2026-03-10"
  },
  "slots": [...]
}
```

---

### 5.5 Appointment Reference Generation

**Purpose:** Create memorable, unique identifiers without storing customer PII.

**Implementation:**

```python
import random
from .models import Appointment

def generate_appointment_ref():
    """
    Generate unique reference in format: BS-XXXXXX
    BS = BarberSync
    XXXXXX = 6-digit random number
    """
    while True:
        random_num = random.randint(100000, 999999)
        ref = f"BS-{random_num}"
        
        # Ensure uniqueness
        if not Appointment.objects.filter(appointment_ref=ref).exists():
            return ref
```

**Why this format?**
- `BS-` prefix clearly identifies the system
- 6 digits = 1,000,000 possible combinations
- Easy to read over phone
- No sequential patterns (harder to guess)

---

## 6. API Design

### 6.1 Endpoint Specification

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| **GET** | `/api/barbers/` | List all active barbers | No |
| **GET** | `/api/availability/` | Get available slots for date range | No |
| **POST** | `/api/appointments/` | Create SOFT_HOLD booking | No |
| **PATCH** | `/api/appointments/{ref}/confirm/` | Customer confirms (SOFT_HOLD → PENDING) | No |
| **GET** | `/api/appointments/{ref}/` | Check appointment status | No |
| **DELETE** | `/api/appointments/{ref}/` | Customer cancels appointment | No |
| **PATCH** | `/api/appointments/{ref}/accept/` | Barber accepts (PENDING → CONFIRMED) | Yes (Barber) |
| **PATCH** | `/api/appointments/{ref}/decline/` | Barber declines (PENDING → CANCELLED) | Yes (Barber) |
| **GET** | `/api/appointments/pending/` | List all pending requests | Yes (Barber) |

---

### 6.2 Request/Response Examples

#### Create Appointment (Soft Hold)

**Request:**
```http
POST /api/appointments/
Content-Type: application/json

{
  "barber_id": "550e8400-e29b-41d4-a716-446655440000",
  "slot_datetime": "2026-02-20T14:00:00Z"
}
```

**Response (201 Created):**
```json
{
  "appointment_ref": "BS-183947",
  "barber": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "display_name": "Barber A"
  },
  "slot_datetime": "2026-02-20T14:00:00Z",
  "status": "SOFT_HOLD",
  "created_at": "2026-02-17T10:30:00Z",
  "expires_at": "2026-02-17T10:35:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "This slot is already booked",
  "code": "SLOT_UNAVAILABLE"
}
```

---

#### Check Appointment Status

**Request:**
```http
GET /api/appointments/BS-183947/
```

**Response (200 OK):**
```json
{
  "appointment_ref": "BS-183947",
  "barber": {
    "display_name": "Barber A"
  },
  "slot_datetime": "2026-02-20T14:00:00Z",
  "status": "CONFIRMED",
  "can_cancel": true,
  "created_at": "2026-02-17T10:30:00Z"
}
```

---

## 7. Security & Compliance

### 7.1 GDPR Compliance

**Zero PII Collection:**
- No names stored
- No email addresses
- No phone numbers
- Only appointment references (non-identifiable)

**Data Controller Responsibilities:**
- Customer controls data via appointment reference
- Right to erasure: Customer can delete appointment using reference
- No data retention beyond business need (auto-delete old appointments)

**Justification:**
Since no PII is collected, the system operates outside traditional GDPR requirements for personal data processing.

---

### 7.2 Database Security

**Connection Security:**
- SSL/TLS enforced for all database connections
- Connection string stored in environment variables (never in code)

**Row Level Security (Supabase):**
```sql
-- Example RLS policy (if using Supabase auth)
CREATE POLICY "Barbers can only see their own appointments"
ON appointments
FOR SELECT
TO authenticated
USING (barber_id = auth.uid());
```

**Backup Strategy:**
- Supabase provides automated daily backups
- Point-in-time recovery available
- Manual backup before major migrations

---

### 7.3 API Security

**Rate Limiting:**
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # Prevent abuse
    }
}
```

**Input Validation:**
- All datetime inputs validated against business hours
- Barber IDs validated against active barbers
- Appointment references validated for format

**CORS Configuration:**
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "https://barbersync-frontend.vercel.app",
]
```

---

## 8. Project Structure

```
barbersync_project/
│
├── manage.py
├── requirements.txt
├── .env (not in git)
├── .gitignore
├── README.md
├── ARCHITECTURE.md (this file)
│
├── barbersync_project/          # Django project settings
│   ├── __init__.py
│   ├── settings.py              # Environment-based configuration
│   ├── urls.py                  # Root URL routing
│   ├── wsgi.py                  # WSGI config for deployment
│   └── asgi.py
│
├── bookings/                    # Main Django app
│   ├── __init__.py
│   ├── models.py                # Barber, Appointment, SystemSetting models
│   ├── serializers.py           # DRF serializers
│   ├── views.py                 # API ViewSets
│   ├── urls.py                  # App-level URLs
│   ├── admin.py                 # Django admin configuration
│   ├── apps.py
│   ├── tests/                   # Unit tests
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_api.py
│   │   └── test_business_logic.py
│   │
│   ├── management/              # Custom Django commands
│   │   └── commands/
│   │       ├── cleanup_expired_holds.py
│   │       └── expire_pending_appointments.py
│   │
│   └── migrations/              # Database migrations
│       └── 0001_initial.py
│
└── static/                      # Static files (if serving frontend)
    └── css/
    └── js/
```

---

## 9. Deployment Architecture

### Development Environment
```
Developer Machine
├── Python 3.12 virtual environment
├── SQLite (for quick local testing)
└── Django dev server (runserver)
```

### Production Environment
```
┌─────────────────────────────────────┐
│         Render.com                  │
│  ┌──────────────────────────────┐   │
│  │  Django Web Service          │   │
│  │  - gunicorn server           │   │
│  │  - Environment variables     │   │
│  │  - Health checks enabled     │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
              │
              │ SSL Connection
              ▼
┌─────────────────────────────────────┐
│       Supabase PostgreSQL           │
│  - Managed instance                 │
│  - Automatic backups                │
│  - Connection pooling               │
└─────────────────────────────────────┘
```

**Environment Variables (`.env`):**
```bash
DEBUG=False
SECRET_KEY=<django-secret-key>
DATABASE_URL=postgresql://<user>:<pass>@<host>:<port>/<db>
ALLOWED_HOSTS=barbersync.onrender.com
CORS_ALLOWED_ORIGINS=https://barbersync-frontend.vercel.app
```

---

## 10. Performance Considerations

### Database Indexing Strategy

**Indexes Created:**
1. Primary keys (automatic): `barbers.id`, `appointments.id`
2. Unique constraint: `appointments.appointment_ref`
3. **Critical:** Partial unique index on `(barber_id, slot_datetime)` for active appointments
4. Foreign key index: `appointments.barber_id`
5. Date range queries: Index on `appointments.slot_datetime`

**Query Optimization:**
```python
# Good: Use select_related for foreign keys
Appointment.objects.select_related('barber').get(appointment_ref=ref)

# Good: Use only() to fetch specific fields
Appointment.objects.only('appointment_ref', 'status', 'slot_datetime')

# Good: Use exists() instead of count() for boolean checks
Appointment.objects.filter(barber_id=1, slot_datetime=time).exists()
```

---

### Caching Strategy (Future Enhancement)

```python
# Cache available slots for 1 minute (reduces DB load)
from django.core.cache import cache

def get_available_slots_cached(barber_id, date):
    cache_key = f"slots_{barber_id}_{date}"
    cached = cache.get(cache_key)
    
    if cached is None:
        cached = calculate_available_slots(barber_id, date)
        cache.set(cache_key, cached, timeout=60)
    
    return cached
```

---

## 11. Monitoring & Observability

### Health Check Endpoint

```python
# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection

@api_view(['GET'])
def health_check(request):
    """Simple health check for monitoring services"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return Response({
            "status": "healthy",
            "database": "connected"
        })
    except Exception as e:
        return Response({
            "status": "unhealthy",
            "error": str(e)
        }, status=500)
```

**URL:** `GET /health/`

---

### Key Metrics to Track

1. **Appointment Creation Rate:** Bookings per hour
2. **Double-Booking Attempts:** Database constraint violations (should be 0)
3. **Soft Hold Expiry Rate:** % of holds that timeout
4. **Barber Response Time:** Average time to accept/decline
5. **API Response Times:** p50, p95, p99 latencies
6. **Database Connection Pool:** Active vs idle connections

---

## 12. Testing Strategy

### Unit Tests
```python
# tests/test_models.py
from django.test import TestCase
from bookings.models import Appointment, Barber

class AppointmentModelTest(TestCase):
    def test_appointment_ref_generation(self):
        """Test unique reference generation"""
        ref = generate_appointment_ref()
        self.assertTrue(ref.startswith('BS-'))
        self.assertEqual(len(ref), 9)  # BS-XXXXXX
    
    def test_prevent_double_booking(self):
        """Test database constraint prevents double-booking"""
        barber = Barber.objects.create(display_name="Test Barber")
        time = timezone.now()
        
        # First booking succeeds
        Appointment.objects.create(
            appointment_ref="BS-111111",
            barber=barber,
            slot_datetime=time,
            status='PENDING'
        )
        
        # Second booking should fail
        with self.assertRaises(IntegrityError):
            Appointment.objects.create(
                appointment_ref="BS-222222",
                barber=barber,
                slot_datetime=time,
                status='PENDING'
            )
```

### Integration Tests
```python
# tests/test_api.py
from rest_framework.test import APITestCase

class BookingAPITest(APITestCase):
    def test_create_soft_hold(self):
        """Test POST /api/appointments/ creates soft hold"""
        response = self.client.post('/api/appointments/', {
            'barber_id': self.barber.id,
            'slot_datetime': '2026-02-20T14:00:00Z'
        })
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('appointment_ref', response.data)
        self.assertEqual(response.data['status'], 'SOFT_HOLD')
```

---

## 13. Future Enhancements

### Phase 2 Features (Post-MVP)
1. **SMS Notifications:** Integrate Twilio for barber alerts
2. **QR Code Generation:** Create printable QR codes for in-shop booking
3. **Analytics Dashboard:** Visualize booking patterns, peak hours
4. **Multi-Location Support:** Extend to support multiple shop locations
5. **Customer "Favorites":** Optional feature to remember preferred barber (cookie-based, no account)

### Technical Debt to Address
1. Add comprehensive logging (structured logging with correlation IDs)
2. Implement proper exception handling with custom error classes
3. Add API versioning (`/api/v1/`)
4. Set up CI/CD pipeline (GitHub Actions → Render)
5. Add end-to-end tests with Playwright/Selenium

---

## 14. Glossary

| Term | Definition |
|------|------------|
| **Soft Hold** | Temporary reservation of a slot (5 min) while customer completes booking |
| **Appointment Reference** | Unique identifier (e.g., BS-183947) used to track bookings without PII |
| **Rolling Window** | Dynamic 21-day booking period that updates daily |
| **Partial Unique Index** | Database index that enforces uniqueness only for specific status values |
| **GDPR** | General Data Protection Regulation (EU privacy law) |
| **PII** | Personally Identifiable Information (names, emails, phones) |

---

## 15. References

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html)
- [GDPR Guidelines](https://gdpr.eu/)
- [Render Deployment Guide](https://render.com/docs/deploy-django)

---

**Document Maintenance:**  
This architecture document should be updated whenever:
- Major technology decisions are made
- Database schema changes significantly
- New API endpoints are added
- Security policies change

**Last Review:** February 2026  
**Next Review:** After Phase 1 completion
