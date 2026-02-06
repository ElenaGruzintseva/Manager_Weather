from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import WeatherData, WeatherFetchLog
from .serializers import WeatherDataSerializer, WeatherFetchRequestSerializer, WeatherFetchLogSerializer
from .tasks import fetch_weather_task
import logging

logger = logging.getLogger(__name__)


class WeatherDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WeatherData.objects.all()
    serializer_class = WeatherDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Опционально: фильтрация по координатам через query params
        queryset = super().get_queryset()
        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')
        if lat and lon:
            try:
                lat_f = float(lat)
                lon_f = float(lon)
                queryset = queryset.filter(latitude=lat_f, longitude=lon_f)
            except ValueError:
                pass  # Игнорируем невалидные параметры
        return queryset

    @action(detail=False, methods=['post'])
    def fetch(self, request):
        """Получить и сохранить данные для координат"""
        serializer = WeatherFetchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']

        task = fetch_weather_task.delay(lat, lon)
        return Response({
            'task_id': task.id,
            'coordinates': (lat, lon)
        }, status=status.HTTP_202_ACCEPTED)


class WeatherFetchLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра логов запросов к внешнему API
    """
    queryset = WeatherFetchLog.objects.all()
    serializer_class = WeatherFetchLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['location', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
