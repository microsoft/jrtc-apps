#!/bin/bash
# GRC_run.sh

export GNB_ADDR=127.0.0.1
export UE1_ADDR=127.0.0.1
export UE2_ADDR=127.0.0.1
export UE3_ADDR=127.0.0.1

export GNB_TX=2000
export UE1_RX=2100
export UE2_RX=2200
export UE3_RX=2300

export GNB_RX=2001
export UE1_TX=2101
export UE2_TX=2201
export UE3_TX=2301

export UE1_PATHLOSS=0
export UE2_PATHLOSS=2
export UE3_PATHLOSS=10

export SLOWDOWNN=2

export SAMPLE_RATE=11520000

python3 /app/GRC_multi_ue_headless.py \
  --gnb-addr $GNB_ADDR \
  --gnb-tx-port $GNB_TX \
  --gnb-rx-port $GNB_RX \
  --ue-addrs $UE1_ADDR $UE2_ADDR $UE3_ADDR \
  --ue-tx-ports $UE1_TX $UE2_TX $UE3_TX \
  --ue-rx-ports $UE1_RX $UE2_RX $UE3_RX \
  --ue-pathloss $UE1_PATHLOSS $UE2_PATHLOSS $UE3_PATHLOSS \
  --slowdown $SLOWDOWNN \
  --samp-rate $SAMPLE_RATE

