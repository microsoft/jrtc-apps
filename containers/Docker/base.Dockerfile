# Shell command to build this image:
# docker build -t ghcr.io/microsoft/jrtc-apps/base/srs:latest -f base.Dockerfile .
# docker push ghcr.io/microsoft/jrtc-apps/base/srs:latest


FROM mcr.microsoft.com/azurelinux/base/core:3.0

ARG DPDK_MACHINE=default

COPY Scripts/mariner-extras.repo /etc/yum.repos.d
RUN tdnf makecache


RUN tdnf install -y libdwarf
RUN tdnf install -y fftw
RUN tdnf install -y fftw-devel
RUN tdnf install -y gtest
RUN tdnf install -y gtest-devel
RUN tdnf install -y gmock-devel
RUN tdnf install -y yaml-cpp-devel
RUN tdnf install -y cmake 
RUN tdnf install -y make 
RUN tdnf install -y gcc 
RUN tdnf install -y g++ 
RUN tdnf install -y pkg-config 
RUN tdnf install -y lksctp-tools*

RUN tdnf install -y python3
RUN tdnf install -y python3-pip
RUN tdnf install -y kernel-headers
RUN tdnf install -y kernel-rt kernel-rt-devel kernel-rt-tools
RUN tdnf install -y binutils
RUN tdnf install -y glibc glibc-devel
RUN tdnf install -y wget ca-certificates tar
RUN tdnf install -y meson python3-pyelftools libnuma libnuma-devel
RUN tdnf install -y rdma-core rdma-core-devel libxdp libbpf libxdp-devel libbpf-devel
RUN tdnf install -y nano jq procps-ng

# Init submodules: git submodule update --init --recursive
# Note: There were some issues with cmake so we just build with make. 
# However, later commits changed the default options and broke the build. 
# We are now locked to a specific commit to avoid this issue.
# In future, we should update to use CMake to configure accordingly. 
ADD mbedtls /opt/mbedtls

WORKDIR /opt/mbedtls
RUN python3 -m pip install --user -r scripts/basic.requirements.txt
RUN make
RUN make install

WORKDIR /opt
RUN wget https://fast.dpdk.org/rel/dpdk-23.11.tar.xz
RUN tar xvf dpdk-23.11.tar.xz dpdk-23.11
WORKDIR /opt/dpdk-23.11
RUN meson setup build -Dmachine=${DPDK_MACHINE}
WORKDIR /opt/dpdk-23.11/build
RUN ninja
RUN meson install
RUN ldconfig