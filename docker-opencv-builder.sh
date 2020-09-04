#!/bin/bash

# Install deps
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y cmake \
    gcc g++ \
    python3-dev python3-numpy \
    libavcodec-dev libavformat-dev libswscale-dev \
    libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev \
    libgtk-3-dev \
    libpng-dev libjpeg-dev libopenexr-dev libtiff-dev libwebp-dev \
    git

# build opencv
git clone https://github.com/opencv/opencv.git \
    && cd opencv \
    && mkdir build /opencv-out \
    && cd build \
    && cmake \
    -DBUILD_TIFF=ON \
    -DBUILD_opencv_java=OFF \
    -DWITH_CUDA=OFF \
    -DWITH_OPENGL=ON \
    -DWITH_OPENCL=ON \
    -DWITH_IPP=ON \
    -DWITH_TBB=ON \
    -DWITH_EIGEN=ON \
    -DWITH_V4L=ON \
    -DWITH_FFMPEG=ON \
    -DBUILD_TESTS=OFF \
    -DBUILD_PERF_TESTS=OFF \
    -DCMAKE_BUILD_TYPE=RELEASE \
    -DCMAKE_INSTALL_PREFIX=/opencv-out \
    ../ \
    && make \
    && make install

# package it
tar --transform 's/dist-packages/site-packages/' czvf /output/opencv-bin.tgz /opencv-out/bin /opencv-out/lib opencv-out/include opencv-out/share
