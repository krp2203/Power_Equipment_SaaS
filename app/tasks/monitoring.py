"""
Operational health checks that run on Celery Beat, independent of any
dealer-facing feature. First one: catch a stuck/dead worker by watching the
task queue depth, since a worker can stop consuming without ever crashing -
Docker's own health signals (RestartCount, Status: running) don't notice
that, and a real backlog builds fast.
"""
import os
import redis
from celery import shared_task
from flask import current_app

# Default Celery queue name (what tasks land in unless a task specifies
# another queue - this app doesn't, so 'celery' is the only one to watch).
QUEUE_NAME = 'celery'

# Redis key used to avoid re-sending the alert email every 5 minutes while
# a backlog persists - one email per hour is plenty to get attention.
ALERT_COOLDOWN_KEY = 'celery_backlog_alert_sent_at'
ALERT_COOLDOWN_SECONDS = 60 * 60


def _redis_client():
    url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    return redis.from_url(url)


@shared_task
def check_queue_backlog():
    """
    Runs every 5 minutes via Celery Beat. Logs the current task queue depth,
    and - if it's above threshold - also emails ken@ (at most once/hour) so a
    stuck worker or a runaway backlog gets noticed in minutes, not days.
    """
    threshold = int(os.getenv('CELERY_QUEUE_ALERT_THRESHOLD', '50'))
    try:
        r = _redis_client()
        depth = r.llen(QUEUE_NAME)
    except Exception as e:
        current_app.logger.error(f"check_queue_backlog: couldn't reach Redis - {e}")
        return {'error': str(e)}

    if depth <= threshold:
        current_app.logger.info(f"Celery queue depth: {depth} (threshold {threshold})")
        return {'depth': depth, 'alerted': False}

    current_app.logger.warning(f"Celery queue backlog: {depth} tasks pending (threshold {threshold}) - "
                                f"a worker may be stuck (see mingle/restart notes in docker-compose.yml)")

    alerted = False
    try:
        r = _redis_client()
        # SET ... NX EX: only sends if no alert was recorded in the last hour.
        if r.set(ALERT_COOLDOWN_KEY, '1', nx=True, ex=ALERT_COOLDOWN_SECONDS):
            from app.core.email import send_admin_alert
            send_admin_alert(
                f"Celery queue backlog: {depth} tasks pending",
                f"The Celery task queue ('{QUEUE_NAME}') has {depth} pending tasks, "
                f"above the alert threshold of {threshold}.\n\n"
                f"This usually means a worker stopped consuming without crashing "
                f"(check `docker compose ps` / `celery -A celery_worker.celery inspect ping`) "
                f"rather than the queue being genuinely busy.\n\n"
                f"If the worker needs restarting, use "
                f"`docker compose up -d --force-recreate worker` - a plain `restart` reuses "
                f"the container hostname and can leave the next worker's Celery mingle "
                f"handshake stuck against stale presence data from the dead process."
            )
            alerted = True
    except Exception as e:
        current_app.logger.error(f"check_queue_backlog: alert email failed - {e}")

    return {'depth': depth, 'alerted': alerted}
