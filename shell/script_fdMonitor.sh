#!/bin/bash

### */5 * * * * /home/powin/SEscripts/script_fdMonitor.sh >> /var/log/tomcat8/script_fdMonitor.log 2>&1

LOG_FILE=/var/log/tomcat8/script_fdMonitor.log
MAX_LINES=2880

PID=$(pgrep -f 'org.apache.catalina.startup.Bootstrap start' | head -1)

if [ -n "$PID" ]; then
  TS=$(date '+%Y-%m-%d %H:%M:%S')
  FD_COUNT=$(ls /proc/$PID/fd | wc -l)
  SOCK_COUNT=$(ls -l /proc/$PID/fd | grep socket: | wc -l)
  echo "$TS pid=$PID fd_count=$FD_COUNT socket_count=$SOCK_COUNT" >> "$LOG_FILE"
else
  echo "$(date '+%Y-%m-%d %H:%M:%S') pid=missing fd_count=NA socket_count=NA" >> "$LOG_FILE"
fi

tail -n "$MAX_LINES" "$LOG_FILE" > /tmp/script_fdMonitor.log.tmp && mv /tmp/script_fdMonitor.log.tmp "$LOG_FILE"

