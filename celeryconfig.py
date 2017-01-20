import os
BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://')
