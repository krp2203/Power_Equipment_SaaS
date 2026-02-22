"""
Celery worker configuration.
This module is used to start the Celery worker with: celery -A celery_worker.celery worker
"""
import os
from app import create_app
from app.core.extensions import celery

# Create Flask app context
app = create_app(os.getenv('FLASK_CONFIG') or 'prod')

# Configure Celery with Flask app context
celery.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Make sure tasks run with Flask app context
class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask
