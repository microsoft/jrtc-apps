FROM mcr.microsoft.com/mirror/docker/library/ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

# Install GNU Radio runtime (no GUI)
RUN apt-get clean -y && apt-get update -y
RUN apt-get install -y gnuradio python3 python3-pip libvolk2-bin && \
    apt-get clean

# Create folders need for gnuradio
RUN mkdir -p /root/.gnuradio /tmp/.gnuradio && chmod -R 777 /root/.gnuradio /tmp/.gnuradio
RUN mkdir -p /root/.gnuradio/prefs
RUN echo "DEFAULT" > /root/.gnuradio/prefs/vmcircbuf_default_factory

# Pre-generate VOLK profile for the generic (portable) kernels to avoid
# SIMD dispatch issues on CPUs different from the image build machine.
# If volk_profile fails (e.g. no CPU match), fall back to generic config.
RUN volk_profile || true
RUN mkdir -p /etc/volk
ENV VOLK_CONFIGPATH=/root/.volk

# Copy your generated Python file
COPY srs_grc/GRC_multi_ue_headless.py /app/GRC_multi_ue_headless.py
COPY srs_grc/GRC_run.sh /app/GRC_run.sh

# Run automatically
ENTRYPOINT ["/app/GRC_run.sh"]