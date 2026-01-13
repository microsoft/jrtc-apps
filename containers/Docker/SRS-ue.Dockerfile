ARG SRSRAN_IMAGE_TAG=latest

FROM ghcr.io/microsoft/jrtc-apps/srs-ue-base:${SRSRAN_IMAGE_TAG}

LABEL org.opencontainers.image.source="https://github.com/microsoft/jrtc-apps"
LABEL org.opencontainers.image.authors="Microsoft Corporation"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.description="SDK for SRSRAN with JBPF, built in ZMQ mode"

# Build srsran 4g
WORKDIR /
ADD srsRAN_4G /srsRAN_4G
WORKDIR /srsRAN_4G/build
RUN cmake ../ -DENABLE_RF_PLUGINS=OFF -DCMAKE_C_COMPILER=/usr/local/gcc-11/bin/gcc -DCMAKE_CXX_COMPILER=/usr/local/gcc-11/bin/g++ -DBOOST_ROOT=/usr/local
RUN make -j`nproc`
RUN make install

RUN tdnf install -y iproute iputils iperf3 ipcalc gettext

WORKDIR /usr/local/bin
COPY srs_ue/run.sh .
COPY srs_ue/set_ue_ip_routes.sh .
COPY srs_ue/ue_zmq.conf.template .
COPY srs_ue/run.sh .
RUN chmod +x run.sh set_ue_ip_routes.sh

ENTRYPOINT ["./run.sh"]