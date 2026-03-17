from celery import Celery
from celery.schedules import crontab
import os

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rabbitmq_demo.settings')

# Create Celery app
app = Celery('rabbitmq_demo')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks
app.autodiscover_tasks()

# Periodic Tasks (using Celery Beat)
app.conf.beat_schedule = {
    # Run cleanup every day at 3 AM
    'cleanup-old-data-daily': {
        'task': 'tasks_app.tasks.cleanup_old_data',
        'schedule': crontab(hour=3, minute=0),
    },

    # Send daily digest at 9 AM
    'send-daily-digest': {
        'task': 'tasks_app.tasks.send_daily_digest',
        'schedule': crontab(hour=9, minute=0),
    },

    # Health check every 5 minutes
    'health-check': {
        'task': 'tasks_app.tasks.health_check',
        'schedule': 300.0, # Every 5 minutes
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify RabbitMQ connection"""
    print(f'Request: {self.request!r}')
    print(f'Broker: {self.app.conf.broker_url}')
    return 'Debug task executed successfully'

