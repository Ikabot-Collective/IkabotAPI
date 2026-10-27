#!/bin/sh
set -eu

# Xvfb signals its parent with USR1 when ready (as in xvfb-run). Tini keeps
# this shell off PID 1, then forwards TERM to Uvicorn after exec below.
trap ':' USR1
(trap '' USR1; exec Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp) &
xvfb_pid=$!
wait || true
if ! kill -0 "$xvfb_pid" 2>/dev/null; then
    echo "Xvfb failed to start" >&2
    exit 1
fi
# Xvfb can signal readiness again after its last client disconnects. Preserve
# SIGUSR1 as ignored across exec so closing Chromium cannot stop Uvicorn.
trap '' USR1
export DISPLAY=:99
exec "$@"
