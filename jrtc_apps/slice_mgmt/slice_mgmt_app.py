# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Slice Management Application for JRTC

This application integrates with the JRTC framework to manage RAN slice
allocations. It subscribes to slice management indication streams, logs slice
allocation data, and periodically issues slice allocation updates. The app
supports both local logging and optional remote logging to Azure Log Analytics.

Key features:
- Initializes a JRTC application with request and indication streams for slice management.
- Sends an initial GET request to retrieve current slice allocations.
- Processes slice allocation indications, logs details, and stores state.
- Periodically sends SET requests to update slice allocations (e.g., swapping slice 0/1 configs).
"""


import time
import json
import os
import sys
import ctypes
import socket
import threading
import datetime as dt
from dataclasses import dataclass, asdict
from typing import Dict
from enum import Enum
import traceback

JRTC_APP_PATH = os.environ.get("JRTC_APP_PATH")
if JRTC_APP_PATH is None:
    raise ValueError("JRTC_APP_PATH not set")
sys.path.append(f"{JRTC_APP_PATH}")

from jrtc_router_stream_id import jrtc_router_stream_id_get_device_id
from jrtc_wrapper_utils import get_ctx_from_capsule

import jrtc_app
from jrtc_app import *


import datetime as dt


# always include the logger modules
logger = sys.modules.get('logger')
from logger import Logger

# always include the params file
params = sys.modules.get('slice_mgmt_app_params')    

if params.la_enabled:
    la_logger = sys.modules.get('la_logger')
    from la_logger import LaLogger, LaLoggerConfig

slice_mgmt = sys.modules.get('slice_mgmt')
from slice_mgmt import slice_mgmt_req, slice_mgmt_ind, slice_t, slice_mgmt_msg_type_GET_SLICE_ALLOC, slice_mgmt_msg_type_SET_SLICE_ALLOC


rlog_enabled = False
log_enabled = True

# create lock.
# This is used by "json_handler" and "app_handler" to ensure they use the resources safely.
app_lock = threading.Lock()


##########################################################################
# Define the state variables for the application
@dataclass
class AppStateVars:
    logger: Logger
    app: JrtcApp
    device: str
    initial_get_requested: bool
    next_set_request_ts: dt.datetime
    slice_allocation: slice_mgmt_ind
    



###########################################################################################
# Class to handle reception of JSON message
###########################################################################################
class JsonUDPServer:

    def __init__(self, ip: str, port: int, state: AppStateVars):
        self.ip = ip
        self.port = port
        self.state = state
        self.running = True
        self.sock = None
        self.start_udp_server_thread()

    def start_udp_server_thread(self):
        self.state.logger.log_msg(True, False, "", f"Starting UDP server thread")
        self.server_thread = threading.Thread(target=self.udp_server)
        self.server_thread.daemon = True  # Allows program to exit
        self.server_thread.start()

    def udp_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.ip, self.port))
            self.state.logger.log_msg(True, False, "", f"UDP server listening on {self.ip}:{self.port}")

            while self.running:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    if len(data) > 0:
                        self.json_handler_func(data.decode())
                except Exception as e:
                    print(f"JsonUDPServer: udp_server: error: {e}", flush=True)
                    traceback.print_exc()
        finally:
            if self.sock:
                self.sock.close()
                self.state.logger.log_msg(True, False, "", "UDP server socket closed")

    def stop(self):
        self.running = False
        if self.sock:
            try:
                # Sending dummy data to unblock recvfrom
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(b'', (self.ip, self.port))
                sock.close()
            except Exception:
                pass
        if self.server_thread:
            self.server_thread.join()
                

    ##########################################################################
    def json_handler_func(self, json_str: str) -> None:

        global rlog_enabled
        global log_enabled

        with app_lock:

            j = json.loads(json_str)

            print(f"json_handler_func : {j}", flush=True)


##########################################################################
def app_handler(timeout: bool, stream_idx: int, data_entry: struct_jrtc_router_data_entry, state: AppStateVars):

    global rlog_enabled
    global log_enabled
    
    try:
        with app_lock:

            timestamp = dt.datetime.now(dt.timezone.utc).isoformat("T", "microseconds")

            ##########################################################################
            # main part of function
            if timeout:

                ## timeout processing
                state.logger.process_timeout()

                # on first entry, issue a GET_SLICE_ALLOC request
                if state.initial_get_requested is False:

                    # send GET to the codelet
    
                    req = slice_mgmt_req()
                    req.msg_type = slice_mgmt_msg_type_GET_SLICE_ALLOC
                    req.has_set_req = False

                    # Convert to raw bytes
                    data_len = ctypes.sizeof(req)
                    data_to_send = ctypes.string_at(ctypes.byref(req), data_len)

                    state.logger.log_msg(True, False, "", "slice_mgmt_app: Sending GET_SLICE_ALLOC request")

                    # Send the GET_SLICE_ALLOC request to the codelet
                    res = jrtc_app_router_channel_send_input_msg(
                        state.app, SLICE_MGMT_REQ_SIDX, data_to_send, data_len
                    )
                    if res == 0:
                        state.initial_get_requested = True

                # Has state.next_set_request_ts been reached.
                # If so, reverse the allocations of slices 0 and 1
                if (state.next_set_request_ts is not None) and (dt.datetime.utcnow() >= state.next_set_request_ts):

                    # state.slice_allocation should be set
                    if state.slice_allocation is None:
                        state.logger.log_msg(True, False, "", "ERROR: state.slice_allocation is None !!")

                    # only do this there are >=2 slices
                    if state.slice_allocation.slice_count >= 2:

                        s0, s1 = state.slice_allocation.slice[0], state.slice_allocation.slice[1]
                        for attr in ("min_prb_policy_ratio", "max_prb_policy_ratio", "priority"):
                            tmp = getattr(s0, attr)
                            setattr(s0, attr, getattr(s1, attr))
                            setattr(s1, attr, tmp)

                        req = slice_mgmt_req()
                        req.msg_type = slice_mgmt_msg_type_SET_SLICE_ALLOC
                        req.has_set_req = True
                        req.set_req.has_sfn = (params.slice_update_sfn is not None)
                        if req.set_req.has_sfn:
                            req.set_req.sfn = params.slice_update_sfn
                        req.set_req.has_slot_index = (params.slice_update_slot_index is not None)
                        if req.set_req.has_slot_index:
                            req.set_req.slot_index = params.slice_update_slot_index
                        req.set_req.slice = state.slice_allocation.slice
                        req.set_req.slice_count = state.slice_allocation.slice_count
                        
                        # Convert to raw bytes
                        data_len = ctypes.sizeof(req)
                        data_to_send = ctypes.string_at(ctypes.byref(req), data_len)

                        state.logger.log_msg(True, False, "", "slice_mgmt_app: Sending SET_SLICE_ALLOC request")

                        # Send the SET_SLICE_ALLOC request to the codelet
                        res = jrtc_app_router_channel_send_input_msg(
                            state.app, SLICE_MGMT_REQ_SIDX, data_to_send, data_len
                        )

                    # clear next_set_request_ts.  It will be re-set when the next indication is received
                    state.next_set_request_ts = None

            else:

                stream_id = data_entry.stream_id
                deviceid = jrtc_router_stream_id_get_device_id(stream_id)
                hostname = os.environ.get("HOSTNAME", "")

                output = {}

                # Check the stream index and process the data accordingly

                #####################################################
                ### Ue contexts

                if stream_idx == SLICE_MGMT_IND_SIDX:

                    state.logger.log_msg(True, False, "", "slice_mgmt_app: Received indication")

                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(slice_mgmt_ind)
                    )
                    data = data_ptr.contents

                    state.logger.log_msg(True, False, "", f"SLICE_MGMT_IND_SIDX: timestamp  {data.timestamp} sfn {data.sfn} slot_index {data.slot_index} num custom slices {data.slice_count}")
                    slices = list(data.slice)
                    for i in range(data.slice_count):
                        state.logger.log_msg(True, False, "", f"  slice {i} : pci  {slices[i].pci} nssai {slices[i].nssai.sst}/{slices[i].nssai.sd} min {slices[i].min_prb_policy_ratio} max {slices[i].max_prb_policy_ratio} priority {slices[i].priority}")
                    
                    # store the current slice allocation
                    state.slice_allocation = data

                    # trigger an update in <params.slice_update_periodicity_secs> seconds
                    state.next_set_request_ts = dt.datetime.utcnow() + dt.timedelta(seconds=params.slice_update_periodicity_secs)

                    state.logger.log_msg(True, False, "", f"Triggering a slice allocation update in {params.slice_update_periodicity_secs} seconds, "
                        "sfn/slot:"
                        f"{'Any' if (params.slice_update_sfn is None) else params.slice_update_sfn}/"
                        f"{'Any' if (params.slice_update_slot_index is None) else params.slice_update_slot_index}")

                else:
                    state.logger.log_msg(True, False, "", f"Unknown stream index: {stream_idx}")
                    output = {
                        "stream_index": stream_idx,
                        "error": "Unknown stream index"
                    }

                    # Send the output to the dashboard
                    state.logger.log_msg(log_enabled, rlog_enabled, "Slice-Mgmt", f"{json.dumps(output)}")

    except Exception as e:
        print(f"app_handler: error: {e}", flush=True)
        traceback.print_exc()



##########################################################################
# Main function to start the app (converted from jrtc_start_app)
def jrtc_start_app(capsule):
    env_ctx = get_ctx_from_capsule(capsule)
    if not env_ctx:
        raise ValueError("Failed to retrieve JrtcAppEnv from capsule")
    device_mapping = env_ctx.device_mapping
    device = device_mapping[0].value.decode("utf-8")
    print(f"Starting JRTC Slice Management app for device: {device}", flush=True)

    global SLICE_MGMT_REQ_SIDX
    global SLICE_MGMT_IND_SIDX

    streams = []

    la_workspace_id = os.environ.get("LA_WORKSPACE_ID", "")
    la_primary_key = os.environ.get("LA_PRIMARY_KEY", "")

    if  (params.la_enabled is False) or la_workspace_id == "" or la_primary_key == "":
        print("Log Analytics workspace ID or primary key not set. Using local logger only.", flush=True)
        la_logger = None
    else:
        print("Log Analytics workspace ID and primary key are set. Will do remote logging to Log Analytics.", flush=True)
        # Create the Log Analytics logger
        la_logger = LaLogger(
            LaLoggerConfig(
                "slice_mgmt",  # Log type
                la_workspace_id,         
                la_primary_key,         
                params.la_msgs_per_batch,
                params.la_bytes_per_batch,
                params.la_tx_timeout_secs,
                params.la_stats_period_secs
            ), 
            dbg=False
        )

    stream_id = "slice_mgmt"
    stream_type = "slice_mgmt"

    hostname = os.environ.get("HOSTNAME", "")

    # Initialize the app
    state = AppStateVars(
        logger=Logger(device, hostname, stream_id, stream_type, remote_logger=la_logger),
        app=None,
        device=device,
        initial_get_requested=False,
        next_set_request_ts=None,
        slice_allocation=None)

    # if LA is configured and intitialised, send to LA, and not write to console.
    # else, write to console
    rlog_enabled = (la_logger is not None)
    log_enabled = (not rlog_enabled)
    

    #####################################################
    ### configure the streams

    last_cnt = 0

    streams.append(JrtcStreamCfg_t(
        JrtcStreamIdCfg_t(
            JRTC_ROUTER_REQ_DEST_NONE,
            1,
            b"slice_mgmt://jbpf_agent/slice_mgmt/slice_mgmt", 
            b"slice_request_map"),
        False,  # is_rx
        None  # No AppChannelCfg
    ))
    SLICE_MGMT_REQ_SIDX = last_cnt
    state.logger.log_msg(True, False, "", f"SLICE_MGMT_REQ_SIDX: {SLICE_MGMT_REQ_SIDX}")
    last_cnt += 1

    streams.append(JrtcStreamCfg_t(
        JrtcStreamIdCfg_t(
            JRTC_ROUTER_REQ_DEST_ANY, 
            JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
            b"slice_mgmt://jbpf_agent/slice_mgmt/slice_mgmt", 
            b"slice_indication_map"),
        True,   # is_rx
        None    # No AppChannelCfg 
    ))
    SLICE_MGMT_IND_SIDX = last_cnt
    state.logger.log_msg(True, False, "", f"SLICE_MGMT_IND_SIDX: {SLICE_MGMT_IND_SIDX}")
    last_cnt += 1

    app_cfg = JrtcAppCfg_t(
        b"slice_mgmt",                                 # context
        100,                                           # q_size
        len(streams),                                  # num_streams
        (JrtcStreamCfg_t * len(streams))(*streams),    # streams
        10.0,                                          # initialization_timeout_secs
        0.25,                                          # sleep_timeout_secs
        2.0                                            # inactivity_timeout_secs
    )

    state.app = jrtc_app_create(capsule, app_cfg, app_handler, state)

    state.logger.log_msg(True, True, "", f"Number of subscribed streams: {len(streams)}")

    # start thread for json udp pp
    if params.json_udp_enabled is True:
        json_udp_server = JsonUDPServer("0.0.0.0", params.json_udp_port, state)

    # run the app - This is blocking until the app exists
    jrtc_app_run(state.app)

    # stop thread for json udp pp
    if params.json_udp_enabled is True:
        json_udp_server.stop()

    # clean up app resources
    jrtc_app_destroy(state.app)

