import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sms_activate_bot.settings')

app = Celery('sms_activate_bot')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# celery beat tasks

# app.conf.beat_schedule = {
#     'add-every-30-seconds': {
#         'task': 'bot_app.tasks.periodic',
#         'schedule': 10.0,
#     },
# }
# app.conf.timezone = 'UTC'
