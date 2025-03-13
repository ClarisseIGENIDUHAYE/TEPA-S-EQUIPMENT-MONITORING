
# deviceApp/celery.py


from celery import Celery
from celery.schedules import crontab

app = Celery('your_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Schedule tasks
app.conf.beat_schedule = {
    'check-devices-every-3-minutes': {
        'task': 'deviceApp.tasks.check_all_devices_connectivity',
        'schedule': crontab(minute='*/3'),  # Run every 15 minutes
    },
}




