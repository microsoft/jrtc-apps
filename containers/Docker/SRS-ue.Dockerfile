ARG BASE_IMAGE_TAG=latest

#=============================
# Stage 1: Build libzmq + czmq
FROM ghcr.io/microsoft/jrtc-apps/base/srs:${BASE_IMAGE_TAG} AS builder

# Install build dependencies
RUN tdnf install -y \
      git autoconf automake libtool pkg-config libuuid-devel make gcc cpp && \
    tdnf clean all

WORKDIR /zmq

# Build libzmq
RUN git clone --depth 1 https://github.com/zeromq/libzmq.git && \
    cd libzmq && \
    ./autogen.sh && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# Build czmq
RUN git clone --depth 1 https://github.com/zeromq/czmq.git && \
    cd czmq && \
    ./autogen.sh && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# =============================
# Stage 2: Runtime Image
# =============================
FROM ghcr.io/microsoft/jrtc-apps/base/srs:${BASE_IMAGE_TAG}

# Copy only installed libs/binaries from builder
COPY --from=builder /usr/local /usr/local


LABEL org.opencontainers.image.source="https://github.com/microsoft/jrtc-apps"
LABEL org.opencontainers.image.authors="Microsoft Corporation"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.description="SDK for SRSRAN with JBPF"

RUN tdnf install -y git make && tdnf clean all

WORKDIR /
RUN git clone https://github.com/srsran/srsRAN_Project.git
WORKDIR /srsRAN_Project/build
RUN cmake ../ -DENABLE_EXPORT=ON -DENABLE_ZEROMQ=ON
RUN make -j`nproc`


# RUN echo "*** Installing packages"
# RUN tdnf upgrade tdnf --refresh -y && tdnf -y update
# RUN tdnf -y install yaml-cpp-static boost-devel clang


# RUN echo "*** Installing relevatn jbpf binaries"
# COPY --from=srsran /src/out /src/out
# COPY --from=srsran /src/include /src/include
# COPY --from=srsran /src/external /src/external
# COPY --from=srsran /usr/lib /usr/lib
# COPY --from=srsran /usr/local/lib /usr/local/lib

# RUN rm -f /usr/local/lib/librte*

# RUN echo "*** Installing relevant jbpf_protobuf binaries"
# COPY --from=jbpf_protobuf_builder /jbpf-protobuf/3p/nanopb /nanopb
# COPY --from=jbpf_protobuf_builder jbpf-protobuf/out/bin/jbpf_protobuf_cli /usr/local/bin/jbpf_protobuf_cli

# RUN tdnf install -y gcc gcc-c++ make python3 python3-pip
# RUN pip install ctypesgen
# RUN python3 -m pip install -r /nanopb/requirements.txt

# ENV JBPF_PROTOBUF_CLI_BIN=/usr/local/bin/jbpf_protobuf_cli
# ENV NANO_PB=/nanopb

# ENV LD_LIBRARY_PATH=/usr/local/lib/:/usr/lib

# ENV JBPF_OUT_DIR=/src/out
# ENV SRSRAN_INC_DIR=/src/include
# ENV SRSRAN_EXTERNAL_DIR=/src/external
# ENV CPP_INC=/usr/include/c++/13.2.0
# ENV VERIFIER_BIN=/src/out/bin/srsran_verifier_cli

WORKDIR /out

ENTRYPOINT ["/bin/bash"]
