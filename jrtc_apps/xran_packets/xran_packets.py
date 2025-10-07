# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import time
import os
import sys
import ctypes
from dataclasses import dataclass

JRTC_APP_PATH = os.environ.get("JRTC_APP_PATH")
if JRTC_APP_PATH is None:
    raise ValueError("JRTC_APP_PATH not set")
sys.path.append(f"{JRTC_APP_PATH}")

import jrtc_app
from jrtc_app import *

# Import the xran_packet_info module
xran_packet_info = sys.modules.get('xran_packet_info')
from xran_packet_info import struct__packet_stats


##########################################################################
# Define the state variables for the application
@dataclass
class AppStateVars:
    app: JrtcApp


##########################################################################
# Handler callback function (this function gets called by the C library)
def app_handler(timeout: bool, stream_idx: int, data_entry: struct_jrtc_router_data_entry, state: AppStateVars):

    XRAN_CODELET_OUT_SIDX = 0

    if timeout:

        ## timeout processing

        pass

    else:

        if stream_idx == XRAN_CODELET_OUT_SIDX:

            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__packet_stats)
            )

            data = data_ptr.contents
            ul_data_stats = data.ul_packet_stats.data_packet_stats
            dl_data_stats = data.dl_packet_stats.data_packet_stats
            dl_control_stats = data.dl_packet_stats.ctrl_packet_stats

            print("----------------------------")
            print(f"Hi App 1: timestamp: {data.timestamp}")
            print(f"DL Ctl: {dl_control_stats.Packet_count} {list(dl_control_stats.packet_inter_arrival_info.hist)}")
            print(f"DL Data: {dl_data_stats.Packet_count} {dl_data_stats.Prb_count} {list(dl_data_stats.packet_inter_arrival_info.hist)}")
            print(f"UL Data: {ul_data_stats.Packet_count} {ul_data_stats.Prb_count} {list(ul_data_stats.packet_inter_arrival_info.hist)}")

       
##########################################################################
# Main function to start the app (converted from jrtc_start_app)
def jrtc_start_app(capsule):

    streams = [
        # GENERATOR_OUT_STREAM_IDX
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"xran_packets_deployment://jbpf_agent/xran_packets/reporter", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        )
    ]

    app_cfg = JrtcAppCfg_t(
        b"xran_packets",                               # context
        100,                                           # q_size
        len(streams),                                  # num_streams
        (JrtcStreamCfg_t * len(streams))(*streams),    # streams
        10.0,                                          # initialization_timeout_secs
        0.25,                                          # sleep_timeout_secs
        2.0                                            # inactivity_timeout_secs
    )

    # Initialize the app
    state = AppStateVars(app=None)
    state.app = jrtc_app_create(capsule, app_cfg, app_handler, state)

    # run the app - This is blocking until the app exists
    jrtc_app_run(state.app)

    # clean up app resources
    jrtc_app_destroy(state.app)

