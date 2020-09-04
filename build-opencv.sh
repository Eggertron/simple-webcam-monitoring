#!/bin/bash

docker run --rm -it \
    -v `pwd`/docker-opencv-builder.sh:/builder.sh \
    -v `pwd`:/output/ \
    ubuntu \
    /builder.sh
