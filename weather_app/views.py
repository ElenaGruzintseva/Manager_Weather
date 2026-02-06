from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import WeatherData
from .serializers import WeatherDataSerializer, WeatherRequestSerializer, BatchWeatherRequestSerializer
from .services.data_service import WeatherDataService
from .tasks import fetch_weather_task
import logging

logger = logging.getLogger(__name__)


class WeatherDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WeatherData.objects.all()
    serializer_class = WeatherDataSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def current(self, request):
        city = request.query_params.get('city')
        if not city:
            return Response({'error': 'City parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        data_service = WeatherDataService()
        weather = data_service.get_latest_weather(city)

        if not weather:
            return Response({'error': f'No weather data found for {city}'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(weather)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Получить историю данных для города"""
        city = request.query_params.get('city')
        days = request.query_params.get('days', 7)

        if not city:
            return Response(
                {'error': 'City parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            days = int(days)
        except ValueError:
            days = 7

        data_service = WeatherDataService()
        history = data_service.get_weather_history(city, days)
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def fetch(self, request):
        """Получить и сохранить данные для города"""
        serializer = WeatherRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        city = serializer.validated_data['city']
        force_update = serializer.validated_data['force_update']

        data_service = WeatherDataService()

        if not force_update:
            cached_weather = data_service.get_latest_weather(city)
            if cached_weather:
                serializer = self.get_serializer(cached_weather)
                return Response({'data': serializer.data, 'source': 'cache'})

        task = fetch_weather_task.delay(city)
        return Response({'task_id': task.id, 'city': city}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def batch_fetch(self, request):
        """Получить данные для нескольких городов"""
        serializer = BatchWeatherRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        cities = serializer.validated_data['cities']
        tasks = {}

        for city in cities:
            task = fetch_weather_task.delay(city)
            tasks[city] = task.id

        return Response({'tasks': tasks}, status=status.HTTP_202_ACCEPTED)
