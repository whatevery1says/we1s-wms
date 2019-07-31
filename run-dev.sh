#!/usr/bin/env bash

# For live development,
# leave container running even if python server is stopped
# https://github.com/docker/compose/issues/1926#issuecomment-422351028
# 
# This script can be used as an entrypoint, e.g. with:
#
# manager:
#   entrypoint: 

trap : TERM INT

python /we1s-wms/run.py

tail -f /dev/null & wait

# For more on configuring flask development containers
# with Docker compose, see:
# https://www.patricksoftwareblog.com/using-docker-for-flask-application-development-not-just-production/
# https://stackoverflow.com/questions/44342741/auto-reloading-flask-server-on-docker
