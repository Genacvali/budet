#!/bin/bash

# Health monitor and auto-restart script for Budget App
# Add to crontab: */5 * * * * /root/budget-app/deploy/health-monitor.sh

LOG_FILE="/var/log/budget/health-monitor.log"
SERVICE_NAME="budget.service"
HEALTH_URL="http://127.0.0.1:8000/api/health"
MAX_MEMORY_MB=500  # Restart if memory usage exceeds this

# Create log file if not exists
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if service is running
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    log "❌ Service $SERVICE_NAME is not running. Starting..."
    systemctl start "$SERVICE_NAME"
    sleep 5
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "✅ Service $SERVICE_NAME restarted successfully"
    else
        log "🔥 CRITICAL: Failed to restart $SERVICE_NAME"
        # Could send alert here (email, Slack, etc.)
    fi
    exit 0
fi

# Check health endpoint
if ! curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    log "❌ Health check failed at $HEALTH_URL. Restarting service..."
    systemctl restart "$SERVICE_NAME"
    sleep 5
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        log "✅ Service restarted and health check passed"
    else
        log "🔥 CRITICAL: Service restart failed, health check still failing"
    fi
    exit 0
fi

# Check memory usage
PID=$(systemctl show --property MainPID --value "$SERVICE_NAME")
if [ "$PID" != "0" ] && [ -n "$PID" ]; then
    MEMORY_KB=$(ps -o rss= -p "$PID" 2>/dev/null | tr -d ' ')
    if [ -n "$MEMORY_KB" ]; then
        MEMORY_MB=$((MEMORY_KB / 1024))
        if [ "$MEMORY_MB" -gt "$MAX_MEMORY_MB" ]; then
            log "⚠️  High memory usage: ${MEMORY_MB}MB > ${MAX_MEMORY_MB}MB. Restarting service..."
            systemctl restart "$SERVICE_NAME"
            sleep 3
            log "🔄 Service restarted due to high memory usage"
        fi
    fi
fi

# Log successful check (every hour to avoid spam)
MINUTE=$(date '+%M')
if [ "$MINUTE" = "00" ]; then
    log "✅ Health check passed - service healthy"
fi