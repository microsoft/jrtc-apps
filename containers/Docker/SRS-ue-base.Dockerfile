ARG BASE_IMAGE_TAG=latest

FROM ghcr.io/microsoft/jrtc-apps/base/srs:${BASE_IMAGE_TAG}

RUN tdnf install -y \
      git autoconf automake libtool pkg-config libuuid-devel make gcc cpp libconfig-devel libxcrypt-devel libconfig-devel which && \
    tdnf clean all
    
# downgrade gcc from 13 to 11
RUN tdnf install -y gcc gcc-c++ make wget tar bzip2 gmp-devel mpfr-devel libmpc-devel
WORKDIR /tmp
RUN wget https://ftp.gnu.org/gnu/gcc/gcc-11.4.0/gcc-11.4.0.tar.xz
RUN tar -xf gcc-11.4.0.tar.xz
WORKDIR /tmp/gcc-11.4.0
RUN ./contrib/download_prerequisites
WORKDIR /tmp/gcc-11.4.0/build
RUN ../configure --disable-multilib --enable-languages=c,c++ --prefix=/usr/local/gcc-11
RUN make -j$(nproc) 
RUN make install
# Point system gcc/g++ to gcc-11
RUN ln -sf /usr/local/gcc-11/bin/gcc /usr/bin/gcc && \
    ln -sf /usr/local/gcc-11/bin/g++ /usr/bin/g++
RUN gcc -v

# manually load boost version
RUN tdnf remove -y boost-devel
WORKDIR /opt
RUN wget https://downloads.sourceforge.net/project/boost/boost/1.83.0/boost_1_83_0.tar.gz
RUN tar xzf boost_1_83_0.tar.gz
WORKDIR /opt/boost_1_83_0
RUN ./bootstrap.sh --with-libraries=program_options
RUN ./b2 cxxflags="-std=c++17" --prefix=/usr/local install

# Build libzmq
WORKDIR /zmq
RUN git clone --depth 1 https://github.com/zeromq/libzmq.git && \
    cd libzmq && \
    ./autogen.sh && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# Build czmq
WORKDIR /zmq
RUN git clone --depth 1 https://github.com/zeromq/czmq.git && \
    cd czmq && \
    ./autogen.sh && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    ldconfig


ENTRYPOINT ["/bin/bash"]
