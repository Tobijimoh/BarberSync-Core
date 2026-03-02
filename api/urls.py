from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BarberViewSet, AppointmentViewSet, SystemSettingViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'barbers', BarberViewSet, basename='barber')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'settings', SystemSettingViewSet, basename='setting')

urlpatterns = [
    path('', include(router.urls)),
]