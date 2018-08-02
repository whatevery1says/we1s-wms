#!/usr/bin/env bash

find ./ -type f -name '*.py' -exec sed -i '' -e 's@mongodb://localhost@mongodb://mongo@g' {} \;
