from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Barber, Appointment, SystemSetting
from .serializers import (
    BarberSerializer,
    AppointmentSerializer,
    CreateAppointmentSerializer,
    SystemSettingSerializer
)


class BarberViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing barbers
    
    GET /api/barbers/ - List all active barbers
    GET /api/barbers/{id}/ - Get specific barber details
    """
    queryset = Barber.objects.filter(is_active=True)
    serializer_class = BarberSerializer
    permission_classes = [AllowAny]  # Anyone can view barbers


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all().select_related('barber')
    serializer_class = AppointmentSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        create_serializer = CreateAppointmentSerializer(data=request.data)
        
        if create_serializer.is_valid():
            appointment = create_serializer.save()
            response_serializer = AppointmentSerializer(appointment)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            create_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'], url_path='status/(?P<ref>[^/.]+)')
    def check_status(self, request, ref=None):
        try:
            appointment = Appointment.objects.select_related('barber').get(
                appointment_ref=ref
            )
            
            return Response({
                'appointment_ref': str(appointment.appointment_ref),
                'barber_name': appointment.barber.display_name,
                'slot_datetime': appointment.slot_datetime,
                'status': appointment.status,
                'created_at': appointment.created_at,
                'can_cancel': appointment.status in ['PENDING', 'CONFIRMED']
            })
            
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found. Please check your reference number.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['delete'], url_path='cancel/(?P<ref>[^/.]+)')
    def cancel_appointment(self, request, ref=None):
        try:
            appointment = Appointment.objects.select_related('barber').get(
                appointment_ref=ref
            )
            
            if appointment.status in ['CANCELLED', 'EXPIRED']:
                return Response(
                    {
                        'error': f'Appointment is already {appointment.status.lower()}.',
                        'status': appointment.status
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            previous_status = appointment.status
            appointment.status = 'CANCELLED'
            appointment.updated_at = timezone.now()
            appointment.save()
            
            return Response({
                'message': 'Appointment cancelled successfully.',
                'appointment_ref': str(appointment.appointment_ref),
                'previous_status': previous_status,
                'new_status': 'CANCELLED'
            })
            
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found. Please check your reference number.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='available-slots')
    def available_slots(self, request):
        barber_id = request.query_params.get('barber_id')
        date_str = request.query_params.get('date')
        
        if not barber_id:
            return Response(
                {'error': 'barber_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not date_str:
            return Response(
                {'error': 'date is required (format: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            barber = Barber.objects.get(id=barber_id, is_active=True)
        except Barber.DoesNotExist:
            return Response(
                {'error': 'Barber not found or not active'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            settings = SystemSetting.objects.first()
            if not settings:
                opening_hour = datetime.strptime('08:00', '%H:%M').time()
                closing_hour = datetime.strptime('20:00', '%H:%M').time()
                slot_duration = 60
            else:
                opening_hour = settings.opening_hour
                closing_hour = settings.closing_hour
                slot_duration = int(settings.slot_duration_minutes)
        except Exception:
            opening_hour = datetime.strptime('08:00', '%H:%M').time()
            closing_hour = datetime.strptime('20:00', '%H:%M').time()
            slot_duration = 60
        
        all_slots = []
        current_time = datetime.combine(query_date, opening_hour)
        end_time = datetime.combine(query_date, closing_hour)
        
        while current_time < end_time:
            all_slots.append(current_time.time())
            current_time += timedelta(minutes=slot_duration)
        
        booked_appointments = Appointment.objects.filter(
            barber_id=barber_id,
            slot_datetime__date=query_date,
            status__in=['PENDING', 'CONFIRMED']
        ).values_list('slot_datetime', flat=True)
        
        booked_slots = [appt.time() for appt in booked_appointments]
        
        available_slots = [
            slot for slot in all_slots 
            if slot not in booked_slots
        ]
        
        return Response({
            'barber': {
                'id': barber.id,
                'display_name': barber.display_name
            },
            'date': date_str,
            'available_slots': [slot.strftime('%H:%M:%S') for slot in available_slots],
            'booked_slots': [slot.strftime('%H:%M:%S') for slot in booked_slots],
            'total_slots': len(all_slots),
            'available_count': len(available_slots),
            'booked_count': len(booked_slots)
        })


class SystemSettingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing system settings
    
    GET /api/settings/ - Get system settings
    """
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [AllowAny]