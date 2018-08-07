#!/usr/bin/env bash

pycodestyle
pylint app/
pydocstyle --match-dir='(?!(static|[^\.].*))'
