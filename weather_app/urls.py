from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WeatherDataViewSet, WeatherFetchLogViewSet

router = DefaultRouter()
router.register(r'weather', WeatherDataViewSet, basename='weather')
router.register(r'logs', WeatherFetchLogViewSet, basename='logs')

urlpatterns = [
    path('', include(router.urls)),
]
