from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import WeatherData, WeatherFetchLog
from .serializers import WeatherDataSerializer, WeatherFetchRequestSerializer, WeatherFetchLogSerializer
from .tasks import fetch_weather_task
import logging

logger = logging.getLogger(__name__)


class WeatherDataViewSet(viewsets.ModelViewSet):
    queryset = WeatherData.objects.select_related().only(
        'id', 'latitude', 'longitude', 'temperature', 'pressure', 'humidity',
        'prec_type', 'prec_strength', 'wind_speed', 'wind_direction',
        'fetched_at', 'created_at', 'updated_at'
    ).order_by('-fetched_at')
    serializer_class = WeatherDataSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

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
                pass
        return queryset

    @swagger_auto_schema(
        method='post',
        operation_summary="Получить и сохранить погоду для координат",
        operation_description="Отправляет задачу в очередь на получение данных о погоде для указанных координат и их сохранение.",
        request_body=WeatherFetchRequestSerializer,
        responses={
            202: openapi.Response(
                description="Задача на получение погоды запланирована",
                examples={
                    "application/json": {
                        "task_id": "abc123...",
                        "coordinates": [55.75396, 37.620393]
                    }
                }
            ),
            400: "Неверный формат данных запроса"
        }
    )
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
    """ViewSet для просмотра логов запросов к внешнему API"""
    queryset = WeatherFetchLog.objects.only(
        'id', 'location', 'status', 'error_summary', 'response_time_ms', 'created_at'
    ).order_by('-created_at')
    serializer_class = WeatherFetchLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['location', 'status', 'created_at']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
