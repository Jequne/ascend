#!/bin/bash
set -euo pipefail

echo "=== Postgres backup started ==="

export AWS_ACCESS_KEY_ID="${S3_ACCESS_KEY_ID}"
export AWS_SECRET_ACCESS_KEY="${S3_SECRET_ACCESS_KEY}"
export RESTIC_PASSWORD="${RESTIC_PASSWORD}"

REPO="${POSTGRES_DB_BUCKET}"
DB="${POSTGRES_DB}"
USER="${POSTGRES_USER}"

LOCK_FILE="/tmp/postgres_backup.lock"
DUMP_FILE="/tmp/${DB}_$(date +%F_%H-%M-%S).dump"

MAX_RETRIES=5
RETRY_DELAY=10


exec 200>"$LOCK_FILE"
flock -n 200 || {
    echo "Backup already running, exit"
    exit 1
}


if ! restic -r "$REPO" snapshots >/dev/null 2>&1; then
    echo "Initializing restic repo..."
    restic -r "$REPO" init
fi


echo "Creating dump..."

pg_dump -h db -U "$USER" -Fc "$DB" > "$DUMP_FILE"

attempt=1

while [ $attempt -le $MAX_RETRIES ]; do
    echo "Restic upload attempt $attempt/$MAX_RETRIES..."

    if restic -r "$REPO" backup \
        "$DUMP_FILE" \
        --tag postgres \
        --tag "$DB"; then

        echo "Backup success"
        break
    fi

    echo "Failed, retrying in ${RETRY_DELAY}s..."
    sleep "$RETRY_DELAY"
    attempt=$((attempt + 1))
done

if [ $attempt -gt $MAX_RETRIES ]; then
    echo "Backup FAILED after retries"
    exit 1
fi


rm -f "$DUMP_FILE"


echo "Running retention policy..."

restic -r "$REPO" forget \
    --keep-daily 7 \
    --keep-weekly 4 \
    --keep-monthly 6 \
    --prune

echo "=== Backup finished successfully ==="