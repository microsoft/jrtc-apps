#!/bin/bash
#
# GRC_run.sh
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
#
# Runs the multi-UE GNU Radio Companion simulation.

set -euo pipefail

# ---- Required Environment Variables ----
required_env_vars=(
  "GNB_ADDR"
  "GNB_TX_PORT"
  "GNB_RX_PORT"
  "UE_ADDRS"
  "UE_TX_PORTS"
  "UE_RX_PORTS"
  "UE_PATHLOSS"
)

for env_var in "${required_env_vars[@]}"; do
    if [[ -z "${!env_var:-}" ]]; then
        echo "ERROR: $env_var is undefined!"
        exit 1
    fi
done

# ---- Internally controlled parameters ----
export SLOWDOWN=2
export SAMPLE_RATE=11520000

echo "Launching GRC multi-UE headless with:"
echo "  GNB_ADDR      = $GNB_ADDR"
echo "  GNB_TX_PORT   = $GNB_TX_PORT"
echo "  GNB_RX_PORT   = $GNB_RX_PORT"
echo "  UE_ADDRS      = $UE_ADDRS"
echo "  UE_TX_PORTS   = $UE_TX_PORTS"
echo "  UE_RX_PORTS   = $UE_RX_PORTS"
echo "  UE_PATHLOSS   = $UE_PATHLOSS"
echo "  SLOWDOWN      = $SLOWDOWN"
echo "  SAMPLE_RATE   = $SAMPLE_RATE"
echo

# ---- Run the Python simulation ----
exec python3 /app/GRC_multi_ue_headless.py \
  --gnb-addr "$GNB_ADDR" \
  --gnb-tx-port "$GNB_TX_PORT" \
  --gnb-rx-port "$GNB_RX_PORT" \
  --ue-addrs "$UE_ADDRS" \
  --ue-tx-ports "$UE_TX_PORTS" \
  --ue-rx-ports "$UE_RX_PORTS" \
  --ue-pathloss "$UE_PATHLOSS" \
  --slowdown "$SLOWDOWN" \
  --samp-rate "$SAMPLE_RATE"
