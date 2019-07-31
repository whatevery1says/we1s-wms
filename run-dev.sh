#!/usr/bin/env bash

# For live development,
# leave container running even if python server is stopped
# https://github.com/docker/compose/issues/1926#issuecomment-422351028

trap : TERM INT

python /we1s-wms/run.py

tail -f /dev/null & wait
