#!/bin/ash
# NOTE: we're using ash shell, not bash! ash is the default shell in Alpine Linux
set -e
echo "Launching App With DebugPy Attached & Port Exposed"

pip install -r debug_requirements.txt

DEBUG_PORT=${DEBUG_PORT:-4000}
if [ ! -z $DEBUG_PAUSE ] && [ "${DEBUG_PAUSE}" != "0" ]; then
    echo "Pausing execution for debugpy compattible degugger to be attached to port: ${DEBUG_PORT}"
    python3 -Xfrozen_modules=off -m debugpy --listen "0.0.0.0:${DEBUG_PORT}" --wait-for-client "$@"
else
    python3 -Xfrozen_modules=off -m debugpy --listen "0.0.0.0:${DEBUG_PORT}" "$@"
fi