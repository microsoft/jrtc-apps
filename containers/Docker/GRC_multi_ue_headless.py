#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0
#
# Headless GNU Radio multi-UE flowgraph with CLI arguments for gNB and UE endpoints
#


#
#
# Data transfer illustration
#f
#
# Downlink (gNB → UEs)
#   gNB transmits DL on port 2000
#   UEs receive DL on ports 2100 / 2200 / 2300
# Uplink (UEs → gNB)
#   UEs transmit UL on ports 2101 / 2201 / 2301
#   gNB receives UL on port 2001
#
# Direction	    Sender	    Receiver	Ports
# -----------------------------------------------------------------
# Downlink	    gNB TX	    UE RX	    2000 → 2100/2200/2300
# Uplink        UE TX       gNB RX      2101/2201/2301 → 2001
#
#

import sys
import signal
from argparse import ArgumentParser
from gnuradio import blocks, gr, zeromq

class multi_ue_scenario(gr.top_block):
    def __init__(self,
                 gnb_addr='127.0.0.1',
                 gnb_tx_port=2000,
                 gnb_rx_port=2001,
                 ue_addrs=('127.0.0.1','127.0.0.1','127.0.0.1'),
                 ue_tx_ports=(2101,2201,2301),
                 ue_rx_ports=(2100,2200,2300),
                 ue_pathloss=(0.0,10.0,20.0),
                 slow_down_ratio=4.0,
                 samp_rate=11520000,
                 zmq_timeout=100,
                 zmq_hwm=-1):

        print("[INFO] Initializing multi_ue_scenario...", flush=True)

        # assert that the confif fields have the same lengths
        num_ues = len(ue_addrs)
        assert len(ue_tx_ports) == num_ues, "ue_tx_ports length must match ue_addrs"
        assert len(ue_rx_ports) == num_ues, "ue_rx_ports length must match ue_addrs"
        assert len(ue_pathloss) == num_ues, "ue_pathloss length must match ue_addrs"

        gr.top_block.__init__(self, "srsRAN_multi_UE", catch_exceptions=True)

        self.zmq_timeout = zmq_timeout
        self.zmq_hwm = zmq_hwm
        self.slow_down_ratio = float(slow_down_ratio)
        self.samp_rate = float(samp_rate)

        print(f"[INFO] Sample rate: {self.samp_rate}, Slowdown: {self.slow_down_ratio}", flush=True)

        if len(ue_pathloss) != 3:
            raise ValueError("ue_pathloss must have 3 values")
        self.ue1_path_loss_db, self.ue2_path_loss_db, self.ue3_path_loss_db = map(float, ue_pathloss)
        print(f"[INFO] UE pathloss: {self.ue1_path_loss_db}, {self.ue2_path_loss_db}, {self.ue3_path_loss_db}", flush=True)

        #
        # Ports Used in the GNU-Radio flow graph
        # Port Direction gNB    srsUE1  srsUE2  srsUE3
        # ---------------------------------------------
        # TX             2000   2101    2201    2301
        # Rx             2001   2100    2200    2300
        #
        #
        # set up sources (receivers) and sinks (transmitters)
        #
        # Flow direction	ZMQ block	Port	Meaning
        # -------------------------------------------------------------
        # UE1 → GR	        req_source	2101	UE1 UL samples
        # UE2 → GR	        req_source	2201	UE2 UL samples
        # UE3 → GR	        req_source	2301	UE3 UL samples
        # gNB → GR	        req_source	2000	gNB DL broadcast samples
        # GR → UE1	        rep_sink	2100	UE1 downlink
        # GR → UE2	        rep_sink	2200	UE2 downlink
        # GR → UE3	        rep_sink	2300	UE3 downlink
        # GR → gNB	        rep_sink	2001	Combined UL to gNB
        #
        # The sources / sinks are written from the perspective of the GRC, so for gNB downlink, it is "receive at the GRC", and for gNB uplink, it is sent from the GRC.
        # Port	            External Meaning	Inside Emulator	            ZMQ Block
        # 2000	            gNB TX (DL)	        Emulator receives gNB DL	req_source
        # 2001	            gNB RX (UL)	        Emulator sends UL to gNB	rep_sink
        # 2101/2201/2301	UE TX (UL)	        Emulator receives UL	    req_source
        # 2100/2200/2300	UE RX (DL)	        Emulator sends DL	        rep_sink        

        print(f"[INFO] Creating gNB dl source -> {gnb_addr}:{gnb_tx_port}", flush=True)
        self.gnb_dl_source = zeromq.req_source(gr.sizeof_gr_complex, 1, f"tcp://{gnb_addr}:{gnb_tx_port}", zmq_timeout, False, zmq_hwm)
        print(f"[INFO] Creating gNB ul sink -> {gnb_addr}:{gnb_rx_port}", flush=True)
        self.gnb_ul_sink = zeromq.rep_sink(gr.sizeof_gr_complex, 1, f"tcp://{gnb_addr}:{gnb_rx_port}", zmq_timeout, False, zmq_hwm)

        self.ue_ul_sources = []
        for i, (addr, tx_port) in enumerate(zip(ue_addrs, ue_tx_ports)):
            print(f"[INFO] Creating UE{i+1} ul source -> {addr}:{tx_port}", flush=True)
            self.ue_ul_sources.append(
                zeromq.req_source(gr.sizeof_gr_complex, 1, f"tcp://{addr}:{tx_port}", zmq_timeout, False, zmq_hwm)
            )
        self.ue_dl_sinks = []
        for i, (addr, rx_port) in enumerate(zip(ue_addrs, ue_rx_ports)):
            print(f"[INFO] Creating UE{i+1} dl sink -> {addr}:{rx_port}", flush=True)
            self.ue_dl_sinks.append(
                zeromq.rep_sink(gr.sizeof_gr_complex, 1, f"tcp://{addr}:{rx_port}", zmq_timeout, False, zmq_hwm)
            )

        # Throttle (after summing UE sources)
        self.blocks_throttle = blocks.throttle(gr.sizeof_gr_complex*1,
                                               self.samp_rate/self.slow_down_ratio,
                                               True)

        # Gain factors for gNB TX path (UE RX)
        self.gains = [10**(-pl/20.0) for pl in ue_pathloss]
        print(f"[INFO] UE Gain factors: {self.gains}", flush=True)

        # pathloss multipliers
        # Each UE needs two gain/attenuation blocks:
        #   Downlink direction: gNB → UE
        #   Uplink direction: UE → gNB
        self.blocks_multiply_const_ul_pathloss = [blocks.multiply_const_cc(k) for k in self.gains]
        self.blocks_multiply_const_dl_pathloss = [blocks.multiply_const_cc(k) for k in self.gains]

        self.blocks_add_xx_0 = blocks.add_vcc(1)

        ##################################################
        # Connections
        ##################################################

        # 
        # Throttle: Only applied to the DL (gNB → UE) because the UL is controlled by the UE sources’ pace.
        # Pathloss blocks: Both DL and UL use multiply_const_cc for attenuation.
        # Adder: Only used for UL to sum multiple UE uplink signals into a single gNB sink.
        # UE sinks and gNB sink: Each ZeroMQ sink has a single input port, so each UE DL receives its own path-loss-scaled signal.

#  Downlink
#                    ┌─────────────────┐
#                    │     gNB DL      │
#                    │  (tcp://gnb:2000) 
#                    └───────┬─────────┘
#                            │
#                            ▼
#                   ┌───────────────────┐
#                   │  Throttle Block   │  <- limits sample rate
#                   └───────┬───────────┘
#                           │
#            ┌──────────────┼──────────────┐
#            ▼              ▼              ▼
# ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
# │ DL Pathloss UE1 │ │ DL Pathloss UE2 │ │ DL Pathloss UE3 │
# └───────┬─────────┘ └───────┬─────────┘ └───────┬─────────┘
#         │                   │                   │
#         ▼                   ▼                   ▼
# ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
# │ UE1 DL Sink  │     │ UE2 DL Sink  │     │ UE3 DL Sink  │
# │ (tcp://:2100)│     │ (tcp://:2200)│     │ (tcp://:2300)│
# └──────────────┘     └──────────────┘     └──────────────┘


#  Uplink

#  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
#  │ UE1 UL Source│     │ UE2 UL Source│     │ UE3 UL Source│
#  │ (tcp://:2101)│     │ (tcp://:2201)│     │ (tcp://:2301)│
#  └───────┬──────┘     └───────┬──────┘     └───────┬──────┘
#          │                    │                    │
#          ▼                    ▼                    ▼
# ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
# │ UL Pathloss UE1 │ │ UL Pathloss UE2 │ │ UL Pathloss UE3 │
# └───────┬─────────┘ └───────┬─────────┘ └───────┬─────────┘
#         │                   │                   │
#         └──────────────┬────┴───────┬───────────┘
#                        ▼            ▼
#                  ┌───────────────────--┐
#                  │   UL Adder Block    │  <- sums all UE UL signals
#                  │ sum(UE1+UE2+UE3 UL) │
#                  └─────────┬───────────┘
#                             │
#                             ▼
#                    ┌─────────────────┐
#                    │     gNB UL      │
#                    │  (tcp://:2001)  │
#                    └─────────────────┘


        # --- Connections ---
        print("[INFO] Connecting blocks...", flush=True)

        # -----------------------------
        # Downlink: gNB → UE
        # -----------------------------

        # 1. Throttle gNB downlink to limit processing to the configured sample rate
        print("[INFO] Connecting gNB-DL-source to throttle...", flush=True)
        self.connect((self.gnb_dl_source, 0), (self.blocks_throttle, 0))

        # 2. Apply per-UE pathloss to the throttled gNB signal
        for ue, m in enumerate(self.blocks_multiply_const_dl_pathloss):
            print(f"[INFO] Connecting throttle to UE{ue+1}-DL-pathloss-block...", flush=True)
            self.connect((self.blocks_throttle, 0), (m, 0))

        # 3. Connect each UE downlink pathloss block to its respective UE sink
        for ue in range(num_ues):
            print(f"[INFO] Connecting UE{ue+1}-DL-pathloss-block to UE{ue+1}-DL-sink...", flush=True)
            self.connect((self.blocks_multiply_const_dl_pathloss[ue], 0), (self.ue_dl_sinks[ue], 0))

        # -----------------------------
        # Uplink: UE → gNB
        # -----------------------------

        # 4. Apply per-UE uplink pathloss to each UE source
        for ue in range(num_ues):
            print(f"[INFO] Connecting UE{ue+1}-UL-source to UE{ue+1}-UL-pathloss-block  ...", flush=True)
            self.connect((self.ue_ul_sources[ue], 0), (self.blocks_multiply_const_ul_pathloss[ue], 0))

        # 5. Sum all UL paths after pathloss scaling
        # The adder combines UE1_UL_scaled + UE2_UL_scaled + UE3_UL_scaled → gNB
        for port, m in enumerate(self.blocks_multiply_const_ul_pathloss):
            print(f"[INFO] Connecting UE{port+1}-UL-pathloss-block to UL-adder at port {port}...", flush=True)
            self.connect((m, 0), (self.blocks_add_xx_0, port))

        # 6. Connect the summed UL signal to gNB's UL sink
        print("[INFO] Connecting UL-adder to gNB-UL-sink...", flush=True)
        self.connect((self.blocks_add_xx_0, 0), (self.gnb_ul_sink, 0))

        print("[INFO] multi_ue_scenario initialized.", flush=True)


def parse_args():
    p = ArgumentParser()
    p.add_argument('--gnb-addr', default='127.0.0.1', help='gNB host/IP')
    p.add_argument('--gnb-tx-port', type=int, default=2000, help='gNB TX port')
    p.add_argument('--gnb-rx-port', type=int, default=2001, help='gNB RX port')
    p.add_argument('--ue-addrs', nargs=3, default=['127.0.0.1']*3, help='UE addresses')
    p.add_argument('--ue-tx-ports', nargs=3, type=int, default=[2101,2201,2301], help='UE TX ports')
    p.add_argument('--ue-rx-ports', nargs=3, type=int, default=[2100,2200,2300], help='UE RX ports')
    p.add_argument('--ue-pathloss', nargs=3, type=float, default=[0,10,20], help='UE pathloss dB')
    p.add_argument('--slowdown', type=float, default=4.0, help='Slow down ratio')
    p.add_argument('--samp-rate', type=float, default=11520000, help='Sample rate')
    p.add_argument('--zmq-timeout', type=int, default=100, help='ZMQ timeout ms')
    p.add_argument('--zmq-hwm', type=int, default=-1, help='ZMQ HWM')
    args = p.parse_args()
    print(f"[INFO] Parsed arguments: {args}", flush=True)
    return args


def main():
    args = parse_args()
    tb = multi_ue_scenario(
        gnb_addr=args.gnb_addr,
        gnb_tx_port=args.gnb_tx_port,
        gnb_rx_port=args.gnb_rx_port,
        ue_addrs=tuple(args.ue_addrs),
        ue_tx_ports=tuple(args.ue_tx_ports),
        ue_rx_ports=tuple(args.ue_rx_ports),
        ue_pathloss=tuple(args.ue_pathloss),
        slow_down_ratio=args.slowdown,
        samp_rate=args.samp_rate,
        zmq_timeout=args.zmq_timeout,
        zmq_hwm=args.zmq_hwm
    )

    def sig_handler(sig=None, frame=None):
        print("[INFO] Caught signal, stopping flowgraph...", flush=True)
        try:
            tb.stop()
            tb.wait()
        except:
            pass
        print("[INFO] Flowgraph stopped.", flush=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    print("[INFO] Starting flowgraph...", flush=True)
    tb.start()
    try:
        tb.wait()
    except KeyboardInterrupt:
        sig_handler()


if __name__ == '__main__':
    print("[INFO] Starting multi_ue_headless.py", flush=True)
    main()
