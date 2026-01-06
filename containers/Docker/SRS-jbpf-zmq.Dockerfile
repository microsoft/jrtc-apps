ARG SRS_JBPF_IMAGE_TAG=latest

# =============================
# Stage 1: Build libzmq + czmq
FROM ghcr.io/microsoft/jrtc-apps/srs-jbpf:${SRS_JBPF_IMAGE_TAG} AS builder

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
FROM ghcr.io/microsoft/jrtc-apps/srs-jbpf:${SRS_JBPF_IMAGE_TAG}

# Copy only installed libs/binaries from builder
COPY --from=builder /usr/local /usr/local

# Install build dependencies
RUN tdnf install -y gettext iproute && \
    tdnf clean all

# Update dynamic linker cache
RUN ldconfig

# Verify installation (optional)
RUN ldconfig -p | grep zmq || true

WORKDIR /src/build
RUN rm -rf * /out
RUN cmake .. -DENABLE_ZEROMQ=ON -DENABLE_JBPF=ON -DINITIALIZE_SUBMODULES=OFF -DCMAKE_C_FLAGS="-Wno-error=unused-variable"
RUN make -j VERBOSE=1
RUN make install

WORKDIR /opt/Scripts

ENTRYPOINT ["/bin/bash"]
