from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_api_project.settings')

app = Celery('weather_api_project')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'periodic-weather-update-every-15-minutes': {
        'task': 'weather_app.tasks.periodic_weather_update',
        'schedule': crontab(minute='*/30'),
    },
    'cleanup-old-logs-every-2-days': {
        'task': 'weather_app.tasks.cleanup_old_weather_logs',
        'schedule': crontab(day_of_month='*/2', hour='*/2'),
    },
}

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
