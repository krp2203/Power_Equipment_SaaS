"""
Operational health checks that run on Celery Beat, independent of any
dealer-facing feature. First one: catch a stuck/dead worker by watching the
task queue depth, since a worker can stop consuming without ever crashing -
Docker's own health signals (RestartCount, Status: running) don't notice
that, and a real backlog builds fast.
"""
import os
import ssl
import socket
import redis
from datetime import datetime, date, timezone
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
                f"(check `docker compose ps` - not `celery inspect`/`status`, which no longer "
                f"work against this worker now that gossip is disabled) "
                f"rather than the queue being genuinely busy.\n\n"
                f"Redeploy it with `scripts/restart_worker.sh` (or "
                f"`docker compose up -d --force-recreate worker` directly) - a plain `restart` "
                f"reuses the container hostname and can leave the next worker's Celery mingle "
                f"handshake stuck against stale presence data from the dead process."
            )
            alerted = True
    except Exception as e:
        current_app.logger.error(f"check_queue_backlog: alert email failed - {e}")

    return {'depth': depth, 'alerted': alerted}


# CT103's cert (bentcrankshaft.com) was issued manually and doesn't auto-renew -
# nothing rotates it before it lapses. This nags well ahead of that date so it
# gets renewed on purpose instead of discovered via a dealer's browser warning.
CERT_HOST = 'bentcrankshaft.com'
CERT_PORT = 443
CERT_CONNECT_TIMEOUT = 10


def _cert_not_after(host, port, timeout):
    """Opens a verified TLS connection and returns the peer cert's notAfter
    as a UTC datetime. Raises ssl.SSLError/ssl.CertificateError if the cert
    is already invalid/expired/mismatched - the caller treats that as its
    own (more urgent) case rather than a network failure."""
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
    # e.g. 'Dec 16 23:59:59 2026 GMT' - notAfter/notBefore are always GMT per
    # the X.509 spec, so strip the literal suffix rather than rely on %Z
    # (unreliable across platforms/locales in strptime).
    not_after_str = cert['notAfter'].replace(' GMT', '')
    return datetime.strptime(not_after_str, '%b %d %H:%M:%S %Y').replace(tzinfo=timezone.utc)


@shared_task
def check_cert_expiry():
    """
    Runs daily via Celery Beat. Warns well before CERT_HOST's TLS certificate
    expires, and separately (daily, until fixed) if it's already invalid -
    a plain days-remaining check would just error out and go silent exactly
    when the cert has already lapsed, which is the one time this matters most.
    """
    threshold_days = int(os.getenv('CERT_EXPIRY_ALERT_DAYS', '21'))
    runbook = (
        "Runbook: ask the CT103 agent to run `certbot --nginx --expand` to reissue it. "
        "If the permanent wildcard fix (certbot-dns-google) has landed by then, this "
        "whole check can be deleted instead."
    )

    try:
        not_after = _cert_not_after(CERT_HOST, CERT_PORT, CERT_CONNECT_TIMEOUT)
    except (ssl.SSLError, ssl.CertificateError) as e:
        current_app.logger.error(f"check_cert_expiry: {CERT_HOST} cert is invalid/expired - {e}")
        alerted = False
        try:
            r = _redis_client()
            # Re-alerts once per calendar day until someone fixes it, rather
            # than only once ever - this is worse than "expiring soon".
            key = f"cert_invalid_alert_sent:{date.today().isoformat()}"
            if r.set(key, '1', nx=True, ex=60 * 60 * 24 * 2):
                from app.core.email import send_admin_alert
                send_admin_alert(
                    f"{CERT_HOST} TLS certificate is already invalid",
                    f"A TLS handshake to {CERT_HOST}:{CERT_PORT} failed certificate "
                    f"validation just now: {e}\n\n"
                    f"This means dealer sites are likely showing a browser security "
                    f"warning right now.\n\n{runbook}"
                )
                alerted = True
        except Exception as e2:
            current_app.logger.error(f"check_cert_expiry: alert email failed - {e2}")
        return {'valid': False, 'alerted': alerted}
    except Exception as e:
        # Network/DNS/timeout - not a cert problem, don't alert on it here.
        current_app.logger.error(f"check_cert_expiry: couldn't check {CERT_HOST} - {e}")
        return {'error': str(e)}

    days_left = (not_after - datetime.now(timezone.utc)).days
    expiry_date = not_after.date().isoformat()

    if days_left > threshold_days:
        current_app.logger.info(f"{CERT_HOST} cert OK: expires {expiry_date} ({days_left} days out)")
        return {'valid': True, 'expiry_date': expiry_date, 'days_left': days_left, 'alerted': False}

    current_app.logger.warning(f"{CERT_HOST} cert expires {expiry_date} - only {days_left} day(s) left")

    alerted = False
    try:
        r = _redis_client()
        # Keyed to the expiry date itself, not a time cooldown: fires exactly
        # once per cert cycle, and automatically starts alerting again on its
        # own once the cert is renewed to a new (different) expiry date - no
        # code change needed when that happens.
        key = f"cert_expiry_alert_sent:{expiry_date}"
        if r.set(key, '1', nx=True, ex=60 * 60 * 24 * 45):
            from app.core.email import send_admin_alert
            send_admin_alert(
                f"{CERT_HOST} certificate expires {expiry_date} ({days_left} days)",
                f"The TLS certificate for {CERT_HOST} expires on {expiry_date} - "
                f"{days_left} day(s) from now. It was issued manually and does not "
                f"auto-renew.\n\n{runbook}"
            )
            alerted = True
    except Exception as e:
        current_app.logger.error(f"check_cert_expiry: alert email failed - {e}")

    return {'valid': True, 'expiry_date': expiry_date, 'days_left': days_left, 'alerted': alerted}
