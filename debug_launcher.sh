#!/bin/ash
# NOTE: we're using ash shell, not bash! ash is the default shell in Alpine Linux
set -e
echo "Launching App With DebugPy Attached & Port Exposed"

pip install -r debug_requirements.txt

# SEE: https://stackoverflow.com/questions/72021088/python-debugging-and-auto-reload-on-docker-container

DEBUG_PORT=${DEBUG_PORT:-4000}
# RELOAD_IGNORE=${RELOAD_IGNORE:-'*/usr/local/lib/*;*/.git/*;*runpy.py;*/site-packages/*'}
# -m watchdog.watchmedo auto-restart -d /app -p '*.py' --recursive --ignore-patterns ${RELOAD_IGNORE} \

if [ ! -z $DEBUG_PAUSE ] && [ "${DEBUG_PAUSE}" != "0" ]; then
    echo "Pausing execution for debugpy compattible degugger to be attached to port: ${DEBUG_PORT}"
    python3 -Xfrozen_modules=off \
        -m debugpy --listen "0.0.0.0:${DEBUG_PORT}" --wait-for-client \
        "$@"
else
    python3 -Xfrozen_modules=off \
        -m debugpy --listen "0.0.0.0:${DEBUG_PORT}" \
        "$@"
fi