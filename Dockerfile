FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv git wget zip unzip \
    openjdk-11-jdk autoconf libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev libssl-dev curl \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash builder
USER builder
WORKDIR /home/builder
RUN pip3 install --user buildozer cython
ENV PATH="/home/builder/.local/bin:${PATH}"
WORKDIR /home/builder/app
