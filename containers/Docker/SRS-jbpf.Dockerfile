# Shell command to build this image:
# docker build -t ghcr.io/microsoft/jrtc-apps/srs-jbpf:latest -f SRS-jbpf.Dockerfile .
# docker push ghcr.io/microsoft/jrtc-apps/srs-jbpf:latest


ARG LIB=dpdk
ARG LIB_VERSION=23.11

ARG BASE_IMAGE_TAG=latest
FROM ghcr.io/microsoft/jrtc-apps/base/srs:${BASE_IMAGE_TAG}

LABEL org.opencontainers.image.source="https://github.com/microsoft/jrtc-apps"
LABEL org.opencontainers.image.authors="Microsoft Corporation"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.description="SRSRAN with JBPF support"

ADD srsRAN_Project /src 

ENV PKG_CONFIG_PATH=/opt/dpdk-23.11/build/meson-private:/usr/lib/pkgconfig:/usr/local/lib/pkgconfig:/usr/local/lib64/pkgconfig:$PKG_CONFIG_PATH

# extra modules required when ENABLE_JBPF=ON
RUN tdnf -y install yaml-cpp-static boost-devel clang doxygen

WORKDIR /src
RUN mkdir build
WORKDIR /src/build
# Temporary fix for failing jbpf tests in RELEASE mode. To be removed when jbpf tests are fixed.
#RUN cmake .. -DENABLE_DPDK=True -DENABLE_JBPF=ON -DINITIALIZE_SUBMODULES=OFF
RUN cmake .. -DENABLE_DPDK=True -DENABLE_JBPF=ON -DINITIALIZE_SUBMODULES=OFF -DCMAKE_C_FLAGS="-Wno-error=unused-variable"
RUN make -j VERBOSE=1
RUN make install

ADD Scripts /opt/Scripts
WORKDIR /opt/Scripts
RUN pip3 install -r requirements.txt

ADD udp_forwarder /udp_forwarder 

ENTRYPOINT [ "run.sh" ]


