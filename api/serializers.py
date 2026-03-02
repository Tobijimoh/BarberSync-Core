from rest_framework import serializers
from .models import Barber, Appointment, SystemSetting
import uuid
from django.utils import timezone


class BarberSerializer(serializers.ModelSerializer):
    """Serializer for Barber model - for viewing barber data"""
    
    class Meta:
        model = Barber
        fields = ['id', 'display_name', 'email_address', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for viewing appointments"""
    barber_name = serializers.CharField(source='barber.display_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'appointment_ref',
            'barber',
            'barber_name',
            'slot_datetime',
            'status',
            'source',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'appointment_ref', 'created_at', 'updated_at']


class CreateAppointmentSerializer(serializers.Serializer):
    """Serializer for creating new appointments"""
    barber_id = serializers.IntegerField(required=True)
    slot_datetime = serializers.DateTimeField(required=True)
    
    def validate_barber_id(self, value):
        """Ensure barber exists and is active"""
        try:
            barber = Barber.objects.get(id=value)
            if not barber.is_active:
                raise serializers.ValidationError("This barber is not currently accepting bookings.")
            return value
        except Barber.DoesNotExist:
            raise serializers.ValidationError("Barber not found.")
    
    def validate_slot_datetime(self, value):
        """Ensure slot is not in the past"""
        if value < timezone.now():
            raise serializers.ValidationError("Cannot book appointments in the past.")
        return value
    
    def validate(self, data):
        """
        Check if the slot is available (not already booked)
        """
        # Check if this exact slot is already taken for this barber
        slot_exists = Appointment.objects.filter(
            barber_id=data['barber_id'],
            slot_datetime=data['slot_datetime'],
            status__in=['PENDING', 'CONFIRMED']  # Only check active appointments
        ).exists()
        
        if slot_exists:
            raise serializers.ValidationError({
                'slot_datetime': 'This time slot is already booked for this barber.'
            })
        
        return data
    
    def create(self, validated_data):
        """
        Create a new appointment with a unique UUID reference
        """
        # Generate unique UUID for appointment reference
        appointment_ref = uuid.uuid4()
        
        # Create the appointment
        appointment = Appointment.objects.create(
            appointment_ref=appointment_ref,
            barber_id=validated_data['barber_id'],
            slot_datetime=validated_data['slot_datetime'],
            status='PENDING',  # New appointments start as PENDING
            source='WEB',      # Created via web API
            created_at=timezone.now()
        )
        
        return appointment


class SystemSettingSerializer(serializers.ModelSerializer):
    """Serializer for system settings"""
    
    class Meta:
        model = SystemSetting
        fields = [
            'id',
            'opening_hour',
            'closing_hour',
            'slot_duration_minutes',
            'booking_window_days',
            'hold_expiry_minutes',
            'barber_accept_hours',
            'updated_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']