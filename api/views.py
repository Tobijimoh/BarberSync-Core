from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone

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
    """
    API endpoint for managing appointments
    
    POST /api/appointments/ - Create new appointment
    GET /api/appointments/ - List all appointments
    GET /api/appointments/{id}/ - Get specific appointment
    """
    queryset = Appointment.objects.all().select_related('barber')
    serializer_class = AppointmentSerializer
    permission_classes = [AllowAny]  # Open for now, secure later
    
    def create(self, request, *args, **kwargs):
        """
        Create a new appointment
        
        Request body:
        {
            "barber_id": 1,
            "slot_datetime": "2026-03-05T14:00:00Z"
        }
        
        Response (201 Created):
        {
            "id": 1,
            "appointment_ref": "uuid-here",
            "barber": 1,
            "barber_name": "Barber A",
            "slot_datetime": "2026-03-05T14:00:00Z",
            "status": "PENDING",
            "source": "WEB",
            "created_at": "2026-03-01T21:30:00Z",
            "updated_at": null
        }
        """
        # Use the CreateAppointmentSerializer for validation
        create_serializer = CreateAppointmentSerializer(data=request.data)
        
        if create_serializer.is_valid():
            # Create the appointment
            appointment = create_serializer.save()
            
            # Use the regular serializer to format the response
            response_serializer = AppointmentSerializer(appointment)
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            create_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'], url_path='by-ref')
    def get_by_reference(self, request, pk=None):
        """
        Get appointment by reference number
        
        GET /api/appointments/{ref}/by-ref/
        """
        try:
            appointment = Appointment.objects.get(appointment_ref=pk)
            serializer = AppointmentSerializer(appointment)
            return Response(serializer.data)
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class SystemSettingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing system settings
    
    GET /api/settings/ - Get system settings
    """
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [AllowAny]