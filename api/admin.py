from django.contrib import admin
from .models import Barber, Appointment, SystemSetting

@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = ['id', 'display_name', 'is_active', 'created_at']
    list_filter = ['is_active']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'appointment_ref', 'barber', 'slot_datetime', 'status', 'created_at']
    list_filter = ['status', 'barber']
    search_fields = ['appointment_ref']

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['id', 'opening_hour', 'closing_hour', 'slot_duration_minutes']