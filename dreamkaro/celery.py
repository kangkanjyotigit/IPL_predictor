import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dreamkaro.settings')

app = Celery('dreamkaro')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Configure periodic tasks
app.conf.beat_schedule = {
    'update-match-statuses': {
        'task': 'matches.tasks.update_match_statuses',
        'schedule': crontab(minute='*/5'),  # Run every 5 minutes
    },
    'cleanup-old-matches': {
        'task': 'matches.tasks.cleanup_old_matches',
        'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
