import uuid
from django.db import models
from django.utils import timezone

class Barber(models.Model):
    """Barber profiles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.TextField()
    email_address = models.TextField()
    login_password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    system_id = models.BigIntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'barbers'
        managed = False  # Table already exists in Supabase
    
    def __str__(self):
        return self.display_name


class Appointment(models.Model):
    """Appointment bookings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment_ref = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    barber = models.ForeignKey(Barber, on_delete=models.RESTRICT, db_column='barber_id')
    slot_datetime = models.DateTimeField()
    status = models.TextField()
    source = models.TextField()  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True) 
    
    class Meta:
        db_table = 'appointments'
        managed = False
    
    def __str__(self):
        return f"{self.appointment_ref} - {self.barber.display_name}"


class SystemSetting(models.Model):
    """System configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opening_hour = models.TimeField()
    closing_hour = models.TimeField() 
    slot_duration_minutes = models.DecimalField(max_digits=10, decimal_places=2)
    booking_window_days = models.DecimalField(max_digits=10, decimal_places=2)
    hold_expiry_minutes = models.DecimalField(max_digits=10, decimal_places=2)
    barber_accept_hours = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'system_settings'
        managed = False
    
    def __str__(self):
        return f"System Settings (ID: {self.id})"