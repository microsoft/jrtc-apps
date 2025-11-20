FROM mcr.microsoft.com/mirror/docker/library/ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

# Install GNU Radio runtime (no GUI)
RUN apt-get clean -y && apt-get update -y
RUN apt-get install -y gnuradio python3 python3-pip && \
    apt-get clean

# Create folders need for gnuradio
RUN mkdir -p /root/.gnuradio /tmp/.gnuradio && chmod -R 777 /root/.gnuradio /tmp/.gnuradio
RUN mkdir -p /root/.gnuradio/prefs
RUN echo "DEFAULT" > /root/.gnuradio/prefs/vmcircbuf_default_factory

# Copy your generated Python file
COPY GRC_multi_ue_headless.py /app/GRC_multi_ue_headless.py
COPY GRC_run.sh /app/GRC_run.sh

# Run automatically
ENTRYPOINT ["/app/GRC_run.sh"]