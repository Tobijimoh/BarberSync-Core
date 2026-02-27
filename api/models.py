from django.db import models

class Barber(models.Model):
    """Barber profiles"""
    display_name = models.CharField(max_length=255)
    email_address = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'barbers'
        managed = False  
    
    def __str__(self):
        return self.display_name


class Appointment(models.Model):
    """Appointment bookings"""
    appointment_ref = models.CharField(max_length=255, unique=True)
    barber = models.ForeignKey(Barber, on_delete=models.RESTRICT, db_column='barber_id')
    slot_datetime = models.DateTimeField()
    status = models.CharField(max_length=50, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'appointments'
        managed = False 
    
    def __str__(self):
        return f"{self.appointment_ref} - {self.barber.display_name}"


class SystemSetting(models.Model):
    """System configuration"""
    opening_hour = models.TimeField()
    closing_hour = models.TimeField()
    slot_duration_minutes = models.IntegerField()
    
    class Meta:
        db_table = 'system_settings'
        managed = False  # Table already exists in Supabase
    
    def __str__(self):
        return "System Settings"