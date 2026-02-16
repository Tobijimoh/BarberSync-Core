# BarberSync - Technical Architecture & System Design

## 1. Executive Summary
BarberSync is a specialized booking engine designed for a two-barber shop environment. The system is engineered for **Zero-Friction Booking**, requiring no user accounts or stored PII (Personally Identifiable Information), while enforcing strict database-level constraints to ensure 100% schedule integrity.

## 2. Technology Stack
- **Engine:** Python 3.12 / Django 6.0
- **API Layer:** Django REST Framework (DRF)
- **Database:** PostgreSQL (Hosted via Supabase)
- **Infrastructure:** Monolithic Backend with managed cloud data-store

## 3. Database Schema Design

### Table: `barbers`
Stores professional profiles available for booking.
- `id`: Primary Key (UUID)
- `display_name`: Public-facing name
- `is_active`: Boolean flag to control schedule visibility

### Table: `appointments`
The central ledger for all scheduling activity.
- `id`: Primary Key (UUID)
- `appointment_ref`: Unique public reference (e.g., BS-8829)
- `barber_id`: Foreign Key → `barbers.id`
- `slot_datetime`: Timestamp of the appointment
- `status`: Enum [SOFT_HOLD, PENDING, CONFIRMED, CANCELLED, EXPIRED]
- `created_at / updated_at`: Timestamps for auditing

#### Data Integrity: Double-Booking Prevention
A **Partial Unique Index** is applied to the database:
`CREATE UNIQUE INDEX unique_active_slot ON appointments (barber_id, slot_datetime) WHERE status IN ('SOFT_HOLD', 'PENDING', 'CONFIRMED');`
This ensures the database physically rejects any attempt to double-book a specific barber at a specific time.

### Table: `system_settings`
Global configuration for business logic parameters.
- `hold_expiry_minutes`: Default 5
- `barber_accept_hours`: Default 24
- `booking_window_days`: Default 21

## 4. Core Business Logic

### 4.1 Soft Hold Mechanism (5-Minute Timeout)
To prevent "race conditions" where two users attempt to book the same slot:
1. When a client selects a slot, a record is created with `status = SOFT_HOLD`.
2. The database constraint locks this slot for other users.
3. If the checkout is not completed within **5 minutes**, a cleanup task reverts the slot to available.

### 4.2 Barber Acceptance Window (24-Hour Window)
1. Upon successful client checkout, status transitions to `PENDING`.
2. The Barber is notified of the request.
3. The Barber has **24 hours** to move the status to `CONFIRMED`.
4. If no action is taken, the system marks the appointment as `EXPIRED` and releases the slot.

### 4.3 Rolling 3-Week Availability
The system dynamically calculates the booking window: `Current_Date + 21 Days`. Validations are enforced at the API level to reject any `slot_datetime` outside this range.

## 5. Planned API Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/availability/` | Returns available slots per barber for the 21-day window |
| **POST** | `/appointments/` | Initiates a `SOFT_HOLD` |
| **PATCH** | `/appointments/{ref}/confirm` | Transitions status to `PENDING` (Client-side) |
| **PATCH** | `/appointments/{ref}/approve` | Transitions status to `CONFIRMED` (Barber-side) |
| **GET** | `/appointments/{ref}/` | Status check for client/barber |

## 6. Compliance & Security
- **Zero PII:** No names, emails, or phone numbers are stored. All interaction is handled via the `appointment_ref`.
- **Database Security:** Row Level Security (RLS) and SSL-enforced connections to Supabase.