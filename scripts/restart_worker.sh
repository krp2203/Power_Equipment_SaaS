#!/bin/bash
#
# Safely redeploy the Celery worker (or beat) container.
#
# `docker compose restart worker` / `docker restart <container>` reuses the
# same container hostname. If the worker was stuck (not crashed - see the
# comment above the `worker:` service in the compose file), the replacement
# process's Celery mingle handshake can hang waiting on stale presence data
# Redis still has under that hostname from the dead one. That's the exact
# failure mode that let a worker sit silent for days without anything
# noticing. `up -d --force-recreate` avoids it by dropping the old container
# (and its hostname) before starting the new one.
#
# IMPORTANT: this must run against the SAME compose project name the stack
# was actually launched with (e.g. `docker compose -p <name> -f <file> up`),
# not whatever `docker compose` would default to from the current directory -
# those can differ, and running against the wrong project name spins up a
# second, disconnected stack (duplicate db/redis/ports) instead of touching
# the running one. This script auto-detects the right project name from
# `docker compose ls` by matching the compose file path; if it can't find
# exactly one match, it stops rather than guessing.
#
# Usage:
#   scripts/restart_worker.sh                          # worker, docker-compose.quick.yml
#   scripts/restart_worker.sh beat                      # beat, docker-compose.quick.yml
#   scripts/restart_worker.sh worker docker-compose.yml # worker, a specific compose file

set -e

SERVICE="${1:-worker}"
COMPOSE_FILE="${2:-docker-compose.quick.yml}"
COMPOSE_FILE_ABS="$(readlink -f "$COMPOSE_FILE" 2>/dev/null || echo "$COMPOSE_FILE")"

PROJECT="$(docker compose ls --format json 2>/dev/null \
    | python3 -c "
import json, sys
target = '$COMPOSE_FILE_ABS'
try:
    projects = json.load(sys.stdin)
except Exception:
    projects = []
matches = [p['Name'] for p in projects if target in p.get('ConfigFiles', '').split(',')]
print(matches[0] if len(matches) == 1 else '')
")"

if [ -z "$PROJECT" ]; then
    echo "❌ Couldn't uniquely identify the running compose project for $COMPOSE_FILE."
    echo "   Run 'docker compose ls' and pass the project explicitly:"
    echo "   docker compose -p <project> -f $COMPOSE_FILE up -d --force-recreate $SERVICE"
    exit 1
fi

echo "🔁 Force-recreating '$SERVICE' in project '$PROJECT' ($COMPOSE_FILE) - NOT a plain restart..."
docker compose -p "$PROJECT" -f "$COMPOSE_FILE" up -d --force-recreate "$SERVICE"

echo "✅ '$SERVICE' recreated."
if [ "$SERVICE" = "worker" ]; then
    echo "🔎 Verifying it's actually consuming (not just running)..."
    sleep 5
    docker compose -p "$PROJECT" -f "$COMPOSE_FILE" exec -T "$SERVICE" celery -A celery_worker.celery inspect ping --timeout 5
fi
