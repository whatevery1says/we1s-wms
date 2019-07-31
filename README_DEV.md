# README-DEV.md
Jeremy Douglass

This details options for deploying the we1s-manager
in a container for live development in the cloud and
with the full mongodb data store.

"dev-manual" is the preferred method (see below).


## integration

This app is developed out of the repo...

https://github.com/whatevery1says/we1s-wms/

...commits are auto-built on
Dockerhub...

https://hub.docker.com/r/jeremydouglass/we1s-manager

...and pulled to harbor via Portainer, where it is
deployed from the 'dockerhub' branch using the `we1s`
stack config:

    #we1s stack
    manager:
      image: 'jeremydouglass/we1s-manager:dockerhub'


## deployment: production

This flask app has not yet been put into production.

https://flask.palletsprojects.com/en/1.1.x/deploying/


## deployment: dev-debug

By default, the repo Dockerfile configures the container to
run the app on start:

    ENTRYPOINT ["python", "/we1s-wms/run.py"]

In this state, the flask app runs automatically whenever
the container starts. Crashing the flask app will kill the
container and spawn a new container.

This already supports quick configuration testing.
With run.py using `app.run(  debug=True)`, live changes
to the python code update live on the server. Such changes
are ephemeral -- they aren't saved, and if the container
restarts they will be lost immediately.


## deployment: dev-continue

**UNTESTED**

For dev testing that needs to restart the flask app
without discarding the container, the Portainer stack
configuration may put the container into
dev mode by overriding the entrypoint:

    manager:
      image: 'jeremydouglass/we1s-manager:dockerhub'
      entrypoint: run-dev.sh

Which follows the flask app with a tail command.

    #!/usr/bin/env bash
    trap : TERM INT
    python /we1s-wms/run.py
    tail -f /dev/null & wait

The flask python process starts on container launch for
convenience, and it may be killed and restarted, but its
live log is not exposed.


## deployment: dev-manual

For dev testing that needs to inspect the flask app log
and/or restart a container without discarding it, the
Portainer stack configuration may put the container into
dev mode by overriding the entrypoint:

    manager:
      image: 'jeremydouglass/we1s-manager:dockerhub'
      entrypoint: tail -f /dev/null

In this configuration, any time a new container is
created (e.g. server restart) the flask app must be
launched manually from a console. From the console:

1. Portainer > Containers > we1s-manager > Console ">_"
2. Connect (with default user)

..launch the app:

        cd /we1s-wms/
        python run.py

Once the app is started in a console, you may:

-  leave the console open to inspect live logging
-  use Ctrl+C to quit the app, returning to shell.
    the server stops but the container still runs.
-  close the browser tab, leaving the app running.
    this loses access to the log

If you close the tab, the app can still be killed manually
by running `top`, noting the lefthand id number of the
`python` process, then killing it with `kill -9 <pid>`.

Alternately, the entire container can be restarted.


## using git with dev deployment

To develop code locally and test in the container,
replace the container app snapshot with a live git clone.
From the container console:

1. Portainer > Containers > we1s-manager > Console ">_"
2. Connect (with default user)

...replace the app with a git clone:

    #!/usr/bin/env bash
    cd /
    rm -r we1s-wms
    git clone https://github.com/whatevery1says/we1s-wms.git

To stage changes from a dev branch for testing, fetch the
new branch and checkout:

        git fetch
        git checkout dev

Periodically `git push` from local to the dev branch, then
`git pull` from the container console.

        git pull

If the server crashes, restart it in a separate console:

        cd /we1s-wms/
        python run.py

