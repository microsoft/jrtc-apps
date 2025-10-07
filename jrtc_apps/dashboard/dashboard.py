# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import time
import json
import os
import sys
import ctypes
import socket
import threading
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
la_logger = sys.modules.get('la_logger')
from la_logger import LaLogger, LaLoggerConfig

# always include the params file
params = sys.modules.get('dashboard_params')    

# always include the ue_contexts_map module
ue_contexts_map = sys.modules.get('ue_contexts_map')    
from ue_contexts_map import UeContextsMap, JbpfNgapProcedure, ngap_procedure_to_str, JbpRrcProcedure, rrc_procedure_to_str

# Import the protobuf py modules
if params.include_ue_contexts:
    ue_contexts = sys.modules.get('ue_contexts')
    from ue_contexts import struct__du_ue_ctx_creation, struct__du_ue_ctx_update_crnti, struct__du_ue_ctx_deletion, \
                            struct__cucp_ue_ctx_creation, struct__cucp_ue_ctx_update, struct__cucp_ue_ctx_deletion, \
                            struct__e1ap_cucp_bearer_ctx_setup, struct__e1ap_cuup_bearer_ctx_setup, struct__e1ap_cuup_bearer_ctx_release

if params.include_perf:
    jbpf_stats_report = sys.modules.get('jbpf_stats_report')
    from jbpf_stats_report import struct__jbpf_out_perf_list
if params.include_rrc:
    rrc_ue_add = sys.modules.get('rrc_ue_add')
    rrc_ue_procedure = sys.modules.get('rrc_ue_procedure')
    rrc_ue_remove = sys.modules.get('rrc_ue_remove')
    rrc_ue_update_context = sys.modules.get('rrc_ue_update_context')
    rrc_ue_update_id = sys.modules.get('rrc_ue_update_id')
    from rrc_ue_add import struct__rrc_ue_add
    from rrc_ue_procedure import struct__rrc_ue_procedure
    from rrc_ue_remove import struct__rrc_ue_remove
    from rrc_ue_update_context import struct__rrc_ue_update_context
    from rrc_ue_update_id import struct__rrc_ue_update_id
if params.include_ngap:
    ngap = sys.modules.get('ngap')
    from ngap import struct__ngap_procedure_started, struct__ngap_procedure_completed, struct__ngap_reset
if params.include_pdcp:
    pdcp_dl_stats = sys.modules.get('pdcp_dl_stats')
    pdcp_ul_stats = sys.modules.get('pdcp_ul_stats')
    from pdcp_dl_stats import struct__dl_stats
    from pdcp_ul_stats import struct__ul_stats
if params.include_rlc:
    rlc_dl_stats = sys.modules.get('rlc_dl_stats')
    rlc_ul_stats = sys.modules.get('rlc_ul_stats')
    from rlc_dl_stats import struct__rlc_dl_stats
    from rlc_ul_stats import struct__rlc_ul_stats
if params.include_mac:
    mac_sched_crc_stats = sys.modules.get('mac_sched_crc_stats')
    mac_sched_bsr_stats = sys.modules.get('mac_sched_bsr_stats')
    mac_sched_phr_stats = sys.modules.get('mac_sched_phr_stats')
    mac_sched_uci_stats = sys.modules.get('mac_sched_uci_stats')
    mac_sched_harq_stats = sys.modules.get('mac_sched_harq_stats')
    from mac_sched_crc_stats import struct__crc_stats
    from mac_sched_bsr_stats import struct__bsr_stats
    from mac_sched_phr_stats import struct__phr_stats
    from mac_sched_uci_stats import struct__uci_stats
    from mac_sched_harq_stats import struct__harq_stats
if params.include_fapi:
    fapi_gnb_dl_config_stats = sys.modules.get('fapi_gnb_dl_config_stats')
    fapi_gnb_ul_config_stats = sys.modules.get('fapi_gnb_ul_config_stats')
    fapi_gnb_crc_stats = sys.modules.get('fapi_gnb_crc_stats')
    fapi_gnb_rach_stats = sys.modules.get('fapi_gnb_rach_stats')
    from fapi_gnb_dl_config_stats import struct__dl_config_stats
    from fapi_gnb_ul_config_stats import struct__ul_config_stats
    from fapi_gnb_crc_stats import struct__crc_stats as struct__fapi_crc_stats
    from fapi_gnb_rach_stats import struct__rach_stats
if params.include_xran:
    xran_packet_info = sys.modules.get('xran_packet_info')
    from xran_packet_info import struct__packet_stats


rlog_enabled = False
log_enabled = True

# create lock.
# This is used by "json_handler" and "app_handler" to ensure they use the resources safely.
app_lock = threading.Lock()


#########################################################################
class RLCMode(Enum):
    RLC_TM = 1  # Transparent Mode
    RLC_UM = 2  # Unacknowledged Mode
    RLC_AM = 3  # Acknowledged Mode
    RLC_UNKNOWN = 4  # Unknown Mode

def rlc_mode_to_str(mode: int) -> str:
    try:
        return RLCMode(mode).name
    except ValueError:
        return "UNKNOWN"

def int_2_RLCMode(m: int) -> RLCMode:
    if m >= 1 and m <= 3:
        return RLCMode(m)
    return RLCMode.RLC_UNKNOWN


class MACHarqEvent(Enum):
    MAC_HARQ_EVENT_TX = 0
    MAC_HARQ_EVENT_RETX = 1
    MAC_HARQ_EVENT_FAILURE = 2

def mac_harq_event_to_str(event: int) -> str:
    try:
        return MACHarqEvent(event).name
    except ValueError:
        return "UNKNOWN"



##########################################################################
# Define the state variables for the application
@dataclass
class AppStateVars:
    logger: Logger
    ue_map: UeContextsMap
    app: JrtcApp
    device: str



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

            context_type = j.get("context_type", None)
            event = j.get("event", None)
            if context_type is None or event is None:
                self.state.logger.log_msg(True, True, "", f"Error: malformed message from Core {json_str}")
                return
            
            if context_type == "amf-ue":

                output = {
                    "timestamp": j.get("timestamp", 0),
                    "stream_index": "CORE-AMF-UE",
                    "core-msg": j
                }   

                self.state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                if event == "ran-ue-remove":

                    self.state.ue_map.hook_core_amf_info_remove_ran(
                        suci=j.get("context", {}).get("suci", None),
                        supi=j.get("context", {}).get("supi", None),
                        home_plmn_id=j.get("context", {}).get("home_plmn_id", None),
                        current_guti_plmn=j.get("context", {}).get("current-guti", {}).get("plmn_id", None),
                        current_guti_amf_id=j.get("context", {}).get("current-guti", {}).get("amf_id", None),
                        current_guti_m_tmsi=j.get("context", {}).get("current-guti", {}).get("m_tmsi", None),
                        next_guti_plmn=j.get("context", {}).get("next-guti", {}).get("plmn_id", None),
                        next_guti_amf_id=j.get("context", {}).get("next-guti", {}).get("amf_id", None),
                        next_guti_m_tmsi=j.get("context", {}).get("next-guti", {}).get("m_tmsi", None),
                        tai_plmn=j.get("context", {}).get("nr_tai", {}).get("plmn_id", None),
                        tai_tac=j.get("context", {}).get("nr_tai", {}).get("tac", None),
                        cgi_plmn=j.get("context", {}).get("nr_cgi", {}).get("plmn_id", None),
                        cgi_cellid=j.get("context", {}).get("nr_cgi", {}).get("cell_id", None)
                    )

                else:

                    self.state.ue_map.hook_core_amf_info(
                        ran_ue_ngap_id=j.get("context", {}).get("ran_ue", {}).get("ran_ue_ngap_id", None),
                        amf_ue_ngap_id=j.get("context", {}).get("ran_ue", {}).get("amf_ue_ngap_id", None),
                        suci=j.get("context", {}).get("suci", None),
                        supi=j.get("context", {}).get("supi", None),
                        home_plmn_id=j.get("context", {}).get("home_plmn_id", None),
                        current_guti_plmn=j.get("context", {}).get("current-guti", {}).get("plmn_id", None),
                        current_guti_amf_id=j.get("context", {}).get("current-guti", {}).get("amf_id", None),
                        current_guti_m_tmsi=j.get("context", {}).get("current-guti", {}).get("m_tmsi", None),
                        next_guti_plmn=j.get("context", {}).get("next-guti", {}).get("plmn_id", None),
                        next_guti_amf_id=j.get("context", {}).get("next-guti", {}).get("amf_id", None),
                        next_guti_m_tmsi=j.get("context", {}).get("next-guti", {}).get("m_tmsi", None),
                        tai_plmn=j.get("context", {}).get("nr_tai", {}).get("plmn_id", None),
                        tai_tac=j.get("context", {}).get("nr_tai", {}).get("tac", None),
                        cgi_plmn=j.get("context", {}).get("nr_cgi", {}).get("plmn_id", None),
                        cgi_cellid=j.get("context", {}).get("nr_cgi", {}).get("cell_id", None)
                    )


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

            else:

                stream_id = data_entry.stream_id
                deviceid = jrtc_router_stream_id_get_device_id(stream_id)
                hostname = os.environ.get("HOSTNAME", "")

                # print(f"{timestamp} :  got data, stream_idx: {stream_idx}, stream_id: {stream_id}, deviceid: {deviceid}")

                output = {}

                # Check the stream index and process the data accordingly

                #####################################################
                ### Ue contexts

                if stream_idx == UECTX_DU_ADD_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__du_ue_ctx_creation)
                    )
                    data = data_ptr.contents
                    state.ue_map.hook_du_ue_ctx_creation(deviceid,
                                    data.du_ue_index,    
                                    data.plmn,
                                    data.pci,
                                    data.crnti,
                                    data.tac,
                                    data.nci)
                    ueid = state.ue_map.getid_by_du_index(deviceid, data.du_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "UECTX_DU_ADD",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict()
                    }            

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")
                
                elif stream_idx == UECTX_DU_UPDATE_CRNTI_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__du_ue_ctx_update_crnti)
                    )
                    data = data_ptr.contents
                    state.ue_map.hook_du_ue_ctx_update_crnti(deviceid, data.du_ue_index, data.crnti)

                    ueid = state.ue_map.getid_by_du_index(deviceid, data.du_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "UECTX_DU_UPDATE_CRNTI",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict()
                    }            

                    if uectx is None:
                        output["du_ue_index"] = data.du_ue_index
                        output["rnti"] = data.rnti

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == UECTX_DU_DEL_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__du_ue_ctx_deletion)
                    )
                    data = data_ptr.contents

                    ueid = state.ue_map.getid_by_du_index(deviceid, data.du_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "UECTX_DU_DEL",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict()
                    }            

                    if uectx is None:
                        output["du_ue_index"] = data.du_ue_index

                    state.ue_map.hook_du_ue_ctx_deletion(deviceid, data.du_ue_index)

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == UECTX_CUCP_ADD_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__cucp_ue_ctx_creation)
                    )
                    data = data_ptr.contents

                    if data.has_pci and data.has_crnti:
                        state.ue_map.hook_cucp_uemgr_ue_add(
                                            deviceid,
                                            data.cucp_ue_index,    
                                            data.plmn,
                                            data.pci,
                                            data.crnti)

                    ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "UECTX_CUCP_ADD",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict()
                    }            

                    if uectx is None:
                        output["cucp_ue_index"] = data.cucp_ue_index

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == UECTX_CUCP_UPDATE_CRNTI_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__cucp_ue_ctx_update)
                    )
                    data = data_ptr.contents
                    state.ue_map.hook_cucp_uemgr_ue_add(
                                        deviceid,
                                        data.cucp_ue_index,    
                                        data.plmn,
                                        data.pci,
                                        data.crnti)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "UECTX_CUCP_UPDATE_CRNTI",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict()
                    }            

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == UECTX_CUCP_DEL_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__cucp_ue_ctx_deletion)
                    )
                    data = data_ptr.contents

                    ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "UECTX_CUCP_DEL",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict()
                    }            

                    if uectx is None:
                        output["cucp_ue_index"] = data.cucp_ue_index

                    state.ue_map.hook_cucp_uemgr_ue_remove(deviceid, data.cucp_ue_index)

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == UECTX_CUCP_E1AP_BEARER_SETUP_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__e1ap_cucp_bearer_ctx_setup)
                    )
                    data = data_ptr.contents
                    state.ue_map.hook_e1_cucp_bearer_context_setup(
                                        deviceid,
                                        data.cucp_ue_index, 
                                        data.cucp_ue_e1ap_id)
                    
                    ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "UECTX_CUCP_E1AP_BEARER_SETUP",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict()
                    }            

                    if uectx is None:
                        output["cucp_ue_index"] = data.cucp_ue_index

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == UECTX_CUUP_E1AP_BEARER_SETUP_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__e1ap_cuup_bearer_ctx_setup)
                    )
                    data = data_ptr.contents
                    state.ue_map.hook_e1_cuup_bearer_context_setup(
                                        deviceid,
                                        data.cuup_ue_index,
                                        data.cucp_ue_e1ap_id,
                                        data.cuup_ue_e1ap_id,
                                        data.success)

                    ueid = state.ue_map.getid_by_cuup_index(deviceid, data.cuup_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "UECTX_CUUP_E1AP_BEARER_SETUP",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        "success": data.success,
                    }            

                    if uectx is None:
                        output["cuup_ue_index"] = data.cuup_ue_index

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == UECTX_CUUP_E1AP_BEARER_DEL_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__e1ap_cuup_bearer_ctx_release)
                    )
                    data = data_ptr.contents

                    ueid = state.ue_map.getid_by_cuup_index(deviceid, data.cuup_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "UECTX_CUUP_E1AP_BEARER_DEL_SIDX",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        "success": data.success,
                    }            

                    if uectx is None:
                        output["cuup_ue_index"] = data.cuup_ue_index

                    state.ue_map.hook_e1_cuup_bearer_context_release(
                                        deviceid,
                                        data.cuup_ue_index,
                                        data.cucp_ue_e1ap_id,
                                        data.cuup_ue_e1ap_id,
                                        data.success)

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                #####################################################
                ### Perf

                elif stream_idx == JBPF_STATS_REPORT_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__jbpf_out_perf_list)
                    )
                    data = data_ptr.contents
                    perfs = list(data.hook_perf)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "JBPF_STATS_REPORT",
                        "meas_period": data.meas_period,
                        "perfs": []
                    }
                    cnt = 0
                    for perf in perfs:
                        output["perfs"].append({
                            "hook_name": perf.hook_name.decode('utf-8'),
                            "num": perf.num,
                            "min": perf.min,
                            "max": perf.max,
                            "hist": list(perf.hist),
                            "p50": perf.p50,
                            "p90": perf.p90,
                            "p95": perf.p95,
                            "p99": perf.p99
                        })
                        cnt += 1
                        if cnt >= data.hook_perf_count:
                            break
                    if len(output["perfs"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")


                #####################################################
                ### RRC

                elif stream_idx == RRC_UE_ADD_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__rrc_ue_add)
                    )
                    data = data_ptr.contents

                    ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "RRC_UE_ADD",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict()
                    }

                    if uectx is None:
                        output["cucp_ue_index"] = data.cucp_ue_index

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == RRC_UE_PROCEDURE_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__rrc_ue_procedure)
                    )
                    data = data_ptr.contents

                    ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "RRC_UE_PROCEDURE",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        "procedure": rrc_procedure_to_str(data.procedure),
                        "success": data.success,
                        "meta": data.meta
                    }

                    if uectx is None:
                        output["cucp_ue_index"] = data.cucp_ue_index

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == RRC_UE_REMOVE_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__rrc_ue_remove)
                    )
                    data = data_ptr.contents

                    ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "RRC_UE_REMOVE",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict()
                    }

                    if uectx is None:
                        output["cucp_ue_index"] = data.cucp_ue_index

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == RRC_UE_UPDATE_CONTEXT_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__rrc_ue_update_context)
                    )
                    data = data_ptr.contents

                    ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "RRC_UE_UPDATE_CONTEXT",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        "cucp_ue_index": data.cucp_ue_index,
                        "old_cucp_ue_index": data.old_cucp_ue_index,
                        "rnti": data.c_rnti,
                        "pci": data.pci,
                        "tac": data.tac,
                        "plmn": data.plmn,
                        "nci": data.nci
                    }
                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == RRC_UE_UPDATE_ID_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__rrc_ue_update_id)
                    )
                    data = data_ptr.contents

                    state.ue_map.add_tmsi(deviceid, data.cucp_ue_index, data.tmsi)
                    ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                    uectx = state.ue_map.getuectx(ueid)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "RRC_UE_UPDATE_ID",
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict()
                    }

                    if uectx is None:
                        output["cucp_ue_index"] = data.cucp_ue_index

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")


                #####################################################
                ### NGAP

                elif stream_idx == NGAP_PROCEDURE_STARTED_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__ngap_procedure_started)
                    )
                    data = data_ptr.contents
                    
                    state.ue_map.hook_ngap_procedure_started(deviceid, data.ue_ctx.cucp_ue_index, 
                                                        data.procedure,
                                                        data.ue_ctx.ran_ue_id, 
                                                        ngap_amf_ue_id = None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id)

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "NGAP_PROCEDURE_STARTED",
                        "ngap_ran_ue_id": None if data.ue_ctx.has_ran_ue_id is False else data.ue_ctx.ran_ue_id,
                        "ngap_amf_ue_id": None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id,
                        "procedure": ngap_procedure_to_str(data.procedure)
                    }

                    ueid = state.ue_map.getid_by_cucp_index(deviceid, data.ue_ctx.cucp_ue_index)
                    uectx = state.ue_map.getuectx(ueid)
                    if uectx is not None:
                        output["ue_id"] = ueid
                        output["ue_ctx"] = None if uectx is None else uectx.concise_dict()

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == NGAP_PROCEDURE_COMPLETED_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__ngap_procedure_completed)
                    )
                    data = data_ptr.contents


                    # if the procedure is not a context release, run it first, so that the UE will be updated
                    if data.procedure != JbpfNgapProcedure.NGAP_PROCEDURE_UE_CONTEXT_RELEASE:
                        state.ue_map.hook_ngap_procedure_completed(deviceid, data.ue_ctx.cucp_ue_index,
                                                                data.procedure,
                                                                data.success,
                                                                data.ue_ctx.ran_ue_id, 
                                                                data.ue_ctx.amf_ue_id)
                    
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "NGAP_PROCEDURE_COMPLETED",
                        "ngap_ran_ue_id": None if data.ue_ctx.has_ran_ue_id is False else data.ue_ctx.ran_ue_id,
                        "ngap_amf_ue_id": None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id,
                        "procedure": ngap_procedure_to_str(data.procedure),
                        "success": data.success
                    }

                    ueid = state.ue_map.getid_by_cucp_index(deviceid, data.ue_ctx.cucp_ue_index)
                    uectx = state.ue_map.getuectx(ueid)
                    if uectx is not None:
                        output["ue_id"] = ueid
                        output["ue_ctx"] = None if uectx is None else uectx.concise_dict()


                    # if the procedure is a context release, run it now
                    if data.procedure == JbpfNgapProcedure.NGAP_PROCEDURE_UE_CONTEXT_RELEASE:
                        state.ue_map.hook_ngap_procedure_completed(deviceid, data.ue_ctx.cucp_ue_index,
                                                                data.procedure,
                                                                data.success,
                                                                data.ue_ctx.ran_ue_id, 
                                                                data.ue_ctx.amf_ue_id)

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == NGAP_RESET_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__ngap_reset)
                    )
                    data = data_ptr.contents

                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "NGAP_RESET",
                        "ngap_ran_ue_id": None if data.ue_ctx.has_ran_ue_id is False else data.ue_ctx.ran_ue_id,
                        "ngap_amf_ue_id": None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id
                    }

                    ueid = state.ue_map.getid_by_ngap_ue_ids(
                                None if data.ue_ctx.has_ran_ue_id is False else data.ue_ctx.ran_ue_id,
                                None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id)
                    uectx = state.ue_map.getuectx(ueid)
                    if uectx is not None:
                        output["ue_id"] = ueid
                        output["ue_ctx"] = None if uectx is None else uectx.concise_dict()

                    state.ue_map.hook_ngap_reset(deviceid, data.ue_ctx.cucp_ue_index, 
                                                ngap_ran_ue_id = None if data.ue_ctx.has_ran_ue_id is False else data.ue_ctx.ran_ue_id,
                                                ngap_amf_ue_id = None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id)

                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")


                #####################################################
                ### RLC
                elif stream_idx == RLC_DL_STATS_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__rlc_dl_stats)
                    )
                    data = data_ptr.contents
                    dl_stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "RLC_DL_STATS",
                        "stats": []
                    }
                    cnt = 0
                    for stat in dl_stats:

                        report_stat = False

                        ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index) 
                        uectx = state.ue_map.getuectx(ueid)

                        s = {
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
                            "is_srb": stat.is_srb,
                            "rb_id": stat.rb_id,
                            "rlc_mode": rlc_mode_to_str(stat.rlc_mode)
                        }

                        if uectx is None:
                            s['du_ue_index'] = stat.du_ue_index

                        if stat.sdu_queue_pkts.count > 0:
                            s["sdu_queue_pkts"] = {
                                "count": stat.sdu_queue_pkts.count,
                                "total": stat.sdu_queue_pkts.total,
                                "avg": stat.sdu_queue_pkts.total / stat.sdu_queue_pkts.count,
                                "min": stat.sdu_queue_pkts.min,
                                "max": stat.sdu_queue_pkts.max
                            }
                            report_stat = True

                        if stat.sdu_queue_bytes.count > 0:
                            s["sdu_queue_bytes"] = {
                                "count": stat.sdu_queue_bytes.count,
                                "total": stat.sdu_queue_bytes.total,
                                "avg": stat.sdu_queue_bytes.total / stat.sdu_queue_bytes.count,
                                "min": stat.sdu_queue_bytes.min,
                                "max": stat.sdu_queue_bytes.max
                            }
                            report_stat = True

                        if stat.sdu_new_bytes.count > 0:
                            s["sdu_new_bytes"] = {
                                "count": stat.sdu_new_bytes.count,
                                "total": stat.sdu_new_bytes.total
                            }
                            report_stat = True

                        if stat.pdu_tx_bytes.count > 0:
                            s["pdu_tx_bytes"] = {
                                "count": stat.pdu_tx_bytes.count,
                                "total": stat.pdu_tx_bytes.total
                            }
                            report_stat = True

                        if stat.sdu_tx_started.count > 0:
                            s["sdu_tx_started"] = {
                                "count": stat.sdu_tx_started.count,
                                "total": stat.sdu_tx_started.total,
                                "avg": stat.sdu_tx_started.total / stat.sdu_tx_started.count,
                                "min": stat.sdu_tx_started.min,
                                "max": stat.sdu_tx_started.max
                            }
                            report_stat = True

                        if stat.sdu_tx_completed.count > 0:
                            s["sdu_tx_completed"] = {
                                "count": stat.sdu_tx_completed.count,
                                "total": stat.sdu_tx_completed.total,
                                "avg": stat.sdu_tx_completed.total / stat.sdu_tx_completed.count,
                                "min": stat.sdu_tx_completed.min,
                                "max": stat.sdu_tx_completed.max
                            }
                            report_stat = True

                        if stat.sdu_tx_delivered.count > 0:
                            s["sdu_tx_delivered"] = {
                                "count": stat.sdu_tx_delivered.count,
                                "total": stat.sdu_tx_delivered.total,
                                "avg": stat.sdu_tx_delivered.total / stat.sdu_tx_delivered.count,
                                "min": stat.sdu_tx_delivered.min,
                                "max": stat.sdu_tx_delivered.max
                            }
                            report_stat = True

                        if (int_2_RLCMode(stat.rlc_mode) == RLCMode.RLC_AM and 
                            stat.am.pdu_retx_bytes.count > 0):
                            s["pdu_retx_bytes"] = {
                                "count": stat.am.pdu_retx_bytes.count,
                                "total": stat.am.pdu_retx_bytes.total
                            }
                            report_stat = True

                        if (int_2_RLCMode(stat.rlc_mode) == RLCMode.RLC_AM and 
                            stat.am.pdu_status_bytes.count > 0):
                            s["pdu_status_bytes"] = {
                                "count": stat.am.pdu_status_bytes.count,
                                "total": stat.am.pdu_status_bytes.total
                            }
                            report_stat = True

                        if (int_2_RLCMode(stat.rlc_mode) == RLCMode.RLC_AM and 
                            stat.am.pdu_retx_count.count > 0):
                            s["pdu_retx_count"] = {
                                "count": stat.am.pdu_retx_count.count,
                                "total": stat.am.pdu_retx_count.total,
                                "avg": stat.am.pdu_retx_count.total / stat.am.pdu_retx_count.count,
                                "min": stat.am.pdu_retx_count.min,
                                "max": stat.am.pdu_retx_count.max
                            }
                            report_stat = True

                        if (int_2_RLCMode(stat.rlc_mode) == RLCMode.RLC_AM and
                            stat.am.pdu_window_pkts.count > 0):
                            s["pdu_window_pkts"] = {
                                "count": stat.am.pdu_window_pkts.count,
                                "total": stat.am.pdu_window_pkts.total,
                                "avg": stat.am.pdu_window_pkts.total / stat.am.pdu_window_pkts.count,
                                "min": stat.am.pdu_window_pkts.min,
                                "max": stat.am.pdu_window_pkts.max
                            }
                            report_stat = True

                        if (int_2_RLCMode(stat.rlc_mode) == RLCMode.RLC_AM and
                            stat.am.pdu_window_bytes.count > 0):
                            s["pdu_window_bytes"] = {
                                "count": stat.am.pdu_window_bytes.count,
                                "total": stat.am.pdu_window_bytes.total,
                                "avg": stat.am.pdu_window_bytes.total / stat.am.pdu_window_bytes.count,
                                "min": stat.am.pdu_window_bytes.min,
                                "max": stat.am.pdu_window_bytes.max
                            }
                            report_stat = True

                        if report_stat:
                            output["stats"].append(s)
                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                    if len(output["stats"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")


                elif stream_idx == RLC_UL_STATS_SIDX:

                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__rlc_ul_stats)
                    )
                    data = data_ptr.contents
                    ul_stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "RLC_UL_STATS",
                        "stats": []
                    }
                    cnt = 0
                    for stat in ul_stats:

                        report_stat = False

                        ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index) 
                        uectx = state.ue_map.getuectx(ueid)

                        s = {
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
                            "is_srb": stat.is_srb,
                            "rb_id": stat.rb_id,
                            "rlc_mode": rlc_mode_to_str(stat.rlc_mode)
                        }

                        if uectx is None:
                            s['du_ue_index'] = stat.du_ue_index

                        if stat.pdu_bytes.count > 0:
                            s["pdu_bytes"] = {
                                "count": stat.pdu_bytes.count,
                                "total": stat.pdu_bytes.total
                            }
                            report_stat = True

                        if stat.sdu_delivered_bytes.count > 0:
                            s["sdu_delivered_bytes"] = {
                                "count": stat.sdu_delivered_bytes.count,
                                "total": stat.sdu_delivered_bytes.total
                            }
                            report_stat = True

                        if stat.sdu_delivered_latency.count > 0:
                            s["sdu_delivered_latency"] = {
                                "count": stat.sdu_delivered_latency.count,
                                "total": stat.sdu_delivered_latency.total,
                                "avg": stat.sdu_delivered_latency.total / stat.sdu_delivered_latency.count,
                                "min": stat.sdu_delivered_latency.min,
                                "max": stat.sdu_delivered_latency.max
                            }
                            report_stat = True

                        if (int_2_RLCMode(stat.rlc_mode) == RLCMode.RLC_UM and
                            stat.um.pdu_window_pkts.count > 0):
                            s["pdu_window_pkts"] = {
                                "count": stat.um.pdu_window_pkts.count,
                                "total": stat.um.pdu_window_pkts.total,
                                "avg": stat.um.pdu_window_pkts.total / stat.um.pdu_window_pkts.count,
                                "min": stat.um.pdu_window_pkts.min,
                                "max": stat.um.pdu_window_pkts.max
                            }
                            report_stat = True

                        if (int_2_RLCMode(stat.rlc_mode) == RLCMode.RLC_AM and
                            stat.am.pdu_window_pkts.count > 0):
                            s["pdu_window_pkts"] = {
                                "count": stat.am.pdu_window_pkts.count,
                                "total": stat.am.pdu_window_pkts.total,
                                "avg": stat.am.pdu_window_pkts.total / stat.am.pdu_window_pkts.count,
                                "min": stat.am.pdu_window_pkts.min,
                                "max": stat.am.pdu_window_pkts.max
                            }
                            report_stat = True

                        if report_stat:
                            output["stats"].append(s)
                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                    if len(output["stats"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                #####################################################
                ### PDCP

                elif stream_idx == PDCP_DL_STATS_SIDX:

                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__dl_stats)
                    )
                    data = data_ptr.contents
                    dl_stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "PDCP_DL_STATS",
                        "stats": []
                    }
                    cnt = 0
                    for stat in dl_stats:

                        report_stat = False

                        # if SRB: cu_ue_index means cucp_ue_index, else cu_ue_index means cuup_ue_index
                        if stat.is_srb:
                            ueid = state.ue_map.getid_by_cucp_index(deviceid, stat.cu_ue_index) 
                            ue_index_key = "cucp_ue_index"
                        else:
                            ueid = state.ue_map.getid_by_cuup_index(deviceid, stat.cu_ue_index)
                            ue_index_key = "cuup_ue_index"
                        uectx = state.ue_map.getuectx(ueid)

                        s = {
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
                            "is_srb": stat.is_srb,
                            "rb_id": stat.rb_id,
                            "rlc_mode": rlc_mode_to_str(stat.rlc_mode)
                        }

                        if uectx is None:
                            s[ue_index_key] = stat.cu_ue_index

                        if stat.sdu_new_bytes.count > 0:
                            s["sdu_new_bytes"] = {
                                "count": stat.sdu_new_bytes.count,
                                "total": stat.sdu_new_bytes.total
                            }
                            report_stat = True

                        if stat.sdu_discarded > 0:
                            s["sdu_discarded"] =  stat.sdu_discarded
                            report_stat = True

                        if stat.data_pdu_tx_bytes.count > 0:
                            s["data_pdu_tx_bytes"] = {
                                "count": stat.data_pdu_tx_bytes.count,
                                "total": stat.data_pdu_tx_bytes.total
                            }
                            report_stat = True

                        if stat.data_pdu_retx_bytes.count > 0:
                            s["data_pdu_retx_bytes"] = {
                                "count": stat.data_pdu_retx_bytes.count,
                                "total": stat.data_pdu_retx_bytes.total
                            }
                            report_stat = True

                        if stat.control_pdu_tx_bytes.count > 0:
                            s["control_pdu_tx_bytes"] = {
                                "count": stat.control_pdu_tx_bytes.count,
                                "total": stat.control_pdu_tx_bytes.total
                            }
                            report_stat = True

                        if stat.has_pdu_window_pkts and stat.pdu_window_pkts.count > 0:
                            s["pdu_window_pkts"] = {
                                "count": stat.pdu_window_pkts.count,
                                "total": stat.pdu_window_pkts.total,
                                "avg": stat.pdu_window_pkts.total / stat.pdu_window_pkts.count,
                                "min": stat.pdu_window_pkts.min,
                                "max": stat.pdu_window_pkts.max
                            }
                            report_stat = True

                        if stat.has_pdu_window_bytes and stat.pdu_window_bytes.count > 0:
                            s["pdu_window_bytes"] = {
                                "count": stat.pdu_window_bytes.count,
                                "total": stat.pdu_window_bytes.total,
                                "avg": stat.pdu_window_bytes.total / stat.pdu_window_bytes.count,
                                "min": stat.pdu_window_bytes.min,
                                "max": stat.pdu_window_bytes.max
                            }
                            report_stat = True

                        if stat.has_sdu_tx_latency and stat.sdu_tx_latency.count > 0:
                            s["sdu_tx_latency"] = {
                                "count": stat.sdu_tx_latency.count,
                                "total": stat.sdu_tx_latency.total,
                                "avg": stat.sdu_tx_latency.total / stat.sdu_tx_latency.count,
                                "min": stat.sdu_tx_latency.min,
                                "max": stat.sdu_tx_latency.max
                            }
                            report_stat = True

                        # Add the stat to the output
                        if report_stat:
                            output["stats"].append(s)
                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                    if len(output["stats"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")


                elif stream_idx == PDCP_UL_STATS_SIDX:

                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__ul_stats)
                    )
                    data = data_ptr.contents
                    ul_stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "PDCP_UL_STATS",
                        "stats": []
                    }
                    cnt = 0
                    for stat in ul_stats:

                        report_stat = False

                        # if SRB: cu_ue_index means cucp_ue_index, else cu_ue_index means cuup_ue_index
                        if stat.is_srb:
                            ueid = state.ue_map.getid_by_cucp_index(deviceid, stat.cu_ue_index) 
                            ue_index_key = "cucp_ue_index"
                        else:
                            ueid = state.ue_map.getid_by_cuup_index(deviceid, stat.cu_ue_index)
                            ue_index_key = "cuup_ue_index"
                        uectx = state.ue_map.getuectx(ueid)

                        s = {
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
                            "is_srb": stat.is_srb,
                            "rb_id": stat.rb_id,
                            "rlc_mode": rlc_mode_to_str(stat.rlc_mode)
                        }

                        if uectx is None:
                            s[ue_index_key] = stat.cu_ue_index

                        if stat.sdu_delivered_bytes.count > 0:
                            s["sdu_delivered_bytes"] = {
                                "count": stat.sdu_delivered_bytes.count,
                                "total": stat.sdu_delivered_bytes.total
                            }
                            report_stat = True

                        if stat.rx_data_pdu_bytes.count > 0:
                            s["rx_data_pdu_bytes"] = {
                                "count": stat.rx_data_pdu_bytes.count,
                                "total": stat.rx_data_pdu_bytes.total
                            }
                            report_stat = True

                        if stat.rx_control_pdu_bytes.count > 0:
                            s["rx_control_pdu_bytes"] = {
                                "count": stat.rx_control_pdu_bytes.count,
                                "total": stat.rx_control_pdu_bytes.total
                            }
                            report_stat = True

                        if stat.pdu_window_pkts.count > 0:
                            s["pdu_window_pkts"] = {
                                "count": stat.pdu_window_pkts.count,
                                "total": stat.pdu_window_pkts.total,
                                "avg": stat.pdu_window_pkts.total / stat.pdu_window_pkts.count,
                                "min": stat.pdu_window_pkts.min,
                                "max": stat.pdu_window_pkts.max
                            }
                            report_stat = True

                        if stat.pdu_window_bytes.count > 0:
                            s["pdu_window_bytes"] = {
                                "count": stat.pdu_window_bytes.count,
                                "total": stat.pdu_window_bytes.total,
                                "avg": stat.pdu_window_bytes.total / stat.pdu_window_bytes.count,
                                "min": stat.pdu_window_bytes.min,
                                "max": stat.pdu_window_bytes.max
                            }
                            report_stat = True

                        if report_stat:
                            output["stats"].append(s)
                        cnt += 1
                        if cnt >= data.stats_count:
                            break

                    if len(output["stats"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")


                #####################################################
                ### MAC

                elif stream_idx == MAC_SCHED_CRC_STATS_SIDX:
                    
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__crc_stats)
                    )
                    data = data_ptr.contents
                    crc_stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "MAC_SCHED_CRC_STATS",
                        "stats": []
                    }
                    cnt = 0
                    for stat in crc_stats:
                        if stat.cnt_tx > 0:
                            ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index)
                            uectx = state.ue_map.getuectx(ueid)
                            s = {
                                "ueid": ueid,
                                "ue_ctx": None if uectx is None else uectx.concise_dict(),
                                "cons_max": stat.cons_max,
                                "succ_rate": stat.succ_tx / stat.cnt_tx,
                                "retx_hist": list(stat.retx_hist),
                                "harq_failure": stat.harq_failure,
                                "min_sinr": stat.min_sinr,
                                "min_rsrp": stat.min_rsrp,
                                "max_sinr": stat.max_sinr,
                                "max_rsrp": stat.max_rsrp,
                                "avg_sinr": stat.sum_sinr / stat.cnt_sinr,
                                "avg_rsrp": stat.sum_rsrp / stat.cnt_rsrp
                            }
                            if uectx is None:
                                s["du_ue_index"] = stat.du_ue_index

                            output["stats"].append(s)
                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                    if len(output["stats"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == MAC_SCHED_BSR_STATS_SIDX:

                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__bsr_stats)
                    )
                    data = data_ptr.contents
                    bsr_stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "MAC_SCHED_BSR_STATS",
                        "stats": []
                    }
                    cnt = 0
                    for stat in bsr_stats:
                        if  stat.cnt > 0:
                            ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index)
                            uectx = state.ue_map.getuectx(ueid)
                            s = {
                                "ueid": ueid,
                                "ue_ctx": None if uectx is None else uectx.concise_dict(),
                                "cnt": stat.cnt,
                                "bytes": stat.bytes,
                            }
                            if uectx is None:
                                s["du_ue_index"] = stat.du_ue_index
                                                    
                            output["stats"].append(s)                    
            
                            cnt += 1
                            if cnt >= data.stats_count:
                                break
                    if len(output["stats"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")
        
                elif stream_idx == MAC_SCHED_PHR_STATS_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__phr_stats)
                    )
                    data = data_ptr.contents
                    phr_stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "MAC_SCHED_PHR_STATS",
                        "stats": []
                    }
                    cnt = 0
                    for stat in phr_stats:
                        if stat.ph_max > 0:
                            ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index)
                            uectx = state.ue_map.getuectx(ueid)
                            s = {
                                "ueid": ueid,
                                "ue_ctx": None if uectx is None else uectx.concise_dict(),
                                "cell_id": stat.cell_id,
                                "ph_min": stat.ph_min,
                                "ph_max": stat.ph_max,
                                "p_cmax_min": stat.p_cmax_min,
                                "p_cmax_max": stat.p_cmax_max
                            }

                            if uectx is None:
                                s["du_ue_index"] = stat.du_ue_index
                                                    
                            output["stats"].append(s)           

                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                    if len(output["stats"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == MAC_SCHED_UCI_STATS_SIDX:
                    
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__uci_stats)
                    )
                    data = data_ptr.contents
                    uci_stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "MAC_SCHED_UCI_STATS",
                        "stats": []
                    }
                    cnt = 0

                    for stat in uci_stats:
                        ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index)
                        uectx = state.ue_map.getuectx(ueid)
                        s ={
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        }
                        if uectx is None:
                            s["du_ue_index"] = stat.du_ue_index,

                        if stat.sr_detected > 0:
                            s["sr_detected"] = stat.sr_detected

                        if stat.has_time_advance_offset and stat.time_advance_offset.count > 0:
                            s["time_advance_offset"] = {
                                "count": stat.time_advance_offset.count,
                                "total": stat.time_advance_offset.total,
                                "avg": stat.time_advance_offset.total / stat.time_advance_offset.count,
                                "min": stat.time_advance_offset.min,
                                "max": stat.time_advance_offset.max
                            }

                        if stat.has_csi:
                            s["csi"] = {}
                            if stat.csi.has_ri and stat.csi.ri.count > 0:
                                s["csi"]["ri"] = {
                                    "count": stat.csi.ri.count,
                                    "total": stat.csi.ri.total,
                                    "avg": stat.csi.ri.total / stat.csi.ri.count,
                                    "min": stat.csi.ri.min,
                                    "max": stat.csi.ri.max
                                }
                            if stat.csi.has_cqi and stat.csi.cqi.count > 0:
                                s["csi"]["cqi"] = {
                                    "count": stat.csi.cqi.count,
                                    "total": stat.csi.cqi.total,
                                    "avg": stat.csi.cqi.total / stat.csi.cqi.count,
                                    "min": stat.csi.cqi.min,
                                    "max": stat.csi.cqi.max
                                }

                        output["stats"].append(s)
                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                    if len(output["stats"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")


                elif stream_idx == MAC_SCHED_DL_HARQ_SIDX:
                    
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__harq_stats)
                    )
                    data = data_ptr.contents
                    harq_stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "MAC_SCHED_DL_HARQ",
                        "stats": []
                    }
                    cnt = 0

                    for stat in harq_stats:
                        ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index)
                        uectx = state.ue_map.getuectx(ueid)
                        s ={
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        }
                        if uectx is None:
                            s["du_ue_index"] = stat.du_ue_index,

                        s["max_nof_harq_retxs"] = stat.max_nof_harq_retxs
                        s["mcs_table"] = stat.mcs_table

                        if stat.cons_retx.count > 0:
                            s["cons_retx"] = {
                                "count": stat.cons_retx.count,
                                "total": stat.cons_retx.total,
                                "avg": stat.cons_retx.total / stat.cons_retx.count,
                                "min": stat.cons_retx.min,
                                "max": stat.cons_retx.max
                            }

                        if stat.mcs.count > 0:
                            s["mcs"] = {
                                "count": stat.mcs.count,
                                "total": stat.mcs.total,
                                "avg": stat.mcs.total / stat.mcs.count,
                                "min": stat.mcs.min,
                                "max": stat.mcs.max
                            }

                        s["perHarqTypeStats"] = {}
                        for i, h in enumerate(stat.perHarqTypeStats):
                            hs = {}
                            s["perHarqTypeStats"][mac_harq_event_to_str(i)] = hs
                            if h.count > 0:
                                if h.tbs_bytes.count > 0:
                                    hs["tbs"] = {
                                        "pkts": h.tbs_bytes.count,
                                        "bytes": h.tbs_bytes.total
                                    }
                                if h.has_cqi and h.cqi.count>0:
                                    hs["cqi"] = {
                                        "count": h.cqi.count,
                                        "total": h.cqi.total,
                                        "avg": h.cqi.total / h.cqi.count,
                                        "min": h.cqi.min,
                                        "max": h.cqi.max
                                    }

                        output["stats"].append(s)
                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                    if len(output["stats"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")


                elif stream_idx == MAC_SCHED_UL_HARQ_SIDX:
                    
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__harq_stats)
                    )
                    data = data_ptr.contents
                    harq_stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "MAC_SCHED_UL_HARQ",
                        "stats": []
                    }
                    cnt = 0

                    for stat in harq_stats:
                        ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index)
                        uectx = state.ue_map.getuectx(ueid)
                        s ={
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        }
                        if uectx is None:
                            s["du_ue_index"] = stat.du_ue_index,

                        s["max_nof_harq_retxs"] = stat.max_nof_harq_retxs
                        s["mcs_table"] = stat.mcs_table

                        if stat.cons_retx.count > 0:
                            s["cons_retx"] = {
                                "count": stat.cons_retx.count,
                                "total": stat.cons_retx.total,
                                "avg": stat.cons_retx.total / stat.cons_retx.count,
                                "min": stat.cons_retx.min,
                                "max": stat.cons_retx.max
                            }

                        if stat.mcs.count > 0:
                            s["mcs"] = {
                                "count": stat.mcs.count,
                                "total": stat.mcs.total,
                                "avg": stat.mcs.total / stat.mcs.count,
                                "min": stat.mcs.min,
                                "max": stat.mcs.max
                            }

                        s["perHarqTypeStats"] = {}
                        for i, h in enumerate(stat.perHarqTypeStats):
                            hs = {}
                            s["perHarqTypeStats"][mac_harq_event_to_str(i)] = hs
                            if h.count > 0:
                                if h.tbs_bytes.count > 0:
                                    hs["tbs"] = {
                                        "pkts": h.tbs_bytes.count,
                                        "bytes": h.tbs_bytes.total
                                    }
                                if h.has_cqi and h.cqi.count>0:
                                    hs["cqi"] = {
                                        "count": h.cqi.count,
                                        "total": h.cqi.total,
                                        "avg": h.cqi.total / h.cqi.count,
                                        "min": h.cqi.min,
                                        "max": h.cqi.max
                                    }

                        output["stats"].append(s)
                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                    if len(output["stats"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")


                #####################################################
                ### FAPI

                elif stream_idx == FAPI_DL_CONFIG_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__dl_config_stats)
                    )
                    data = data_ptr.contents
                    stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "FAPI_DL_CONFIG",
                        "ues": []
                    }
                    cnt = 0
                    for stat in stats:
                        if stat.rnti > 0:
                            ueid = state.ue_map.getid_by_pci_rnti(stat.cell_id, stat.rnti)                    
                            uectx = state.ue_map.getuectx(ueid)
                            s = {
                                "cell_id": stat.cell_id,
                                "ueid": ueid,
                                "ue_ctx": None if uectx is None else uectx.concise_dict(),
                                "l1_dlc_tx": stat.l1_dlc_tx,
                                "l1_prb_min": stat.l1_prb_min,
                                "l1_prb_max": stat.l1_prb_max,
                                "l1_prb_avg": stat.l1_prb_avg / stat.l1_cnt if stat.l1_cnt > 0 else 0,
                                "l1_tbs_min": stat.l1_tbs_min,
                                "l1_tbs_max": stat.l1_tbs_max,
                                "l1_tbs_avg": stat.l1_tbs_avg / stat.l1_cnt if stat.l1_cnt > 0 else 0,
                                "l1_mcs_min": stat.l1_mcs_min,
                                "l1_mcs_max": stat.l1_mcs_max,
                                "l1_mcs_avg": stat.l1_mcs_avg / stat.l1_cnt if stat.l1_cnt > 0 else 0,
                                "l1_ant_avg": stat.l1_ant_avg / stat.l1_cnt if stat.l1_cnt > 0 else 0,
                                "l1_dlc_prb_hist": list(stat.l1_dlc_prb_hist),
                                "l1_dlc_mcs_hist": list(stat.l1_dlc_mcs_hist),
                                "l1_dlc_tbs_hist": list(stat.l1_dlc_tbs_hist),
                                "l1_dlc_ant_hist": list(stat.l1_dlc_ant_hist)
                            }

                            if uectx is None:
                                s["rnti"] = stat.rnti
                                                    
                            output["ues"].append(s)                    
                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                    if len(output["ues"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == FAPI_UL_CONFIG_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__ul_config_stats)
                    )
                    data = data_ptr.contents
                    stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "FAPI_UL_CONFIG",
                        "ues": []
                    }
                    cnt = 0
                    for stat in stats:
                        if stat.rnti > 0:
                            ueid = state.ue_map.getid_by_pci_rnti(stat.cell_id, stat.rnti)                    
                            uectx = state.ue_map.getuectx(ueid)
                            s = {
                                "cell_id": stat.cell_id,
                                "ueid": ueid,
                                "ue_ctx": None if uectx is None else uectx.concise_dict(),
                                "l1_ulc_tx": stat.l1_ulc_tx,
                                "l1_prb_min": stat.l1_prb_min,
                                "l1_prb_max": stat.l1_prb_max,
                                "l1_prb_avg": stat.l1_prb_avg / stat.l1_cnt if stat.l1_cnt > 0 else 0,
                                "l1_tbs_min": stat.l1_tbs_min,
                                "l1_tbs_max": stat.l1_tbs_max,
                                "l1_tbs_avg": stat.l1_tbs_avg / stat.l1_cnt if stat.l1_cnt > 0 else 0,
                                "l1_mcs_min": stat.l1_mcs_min,
                                "l1_mcs_max": stat.l1_mcs_max,
                                "l1_mcs_avg": stat.l1_mcs_avg / stat.l1_cnt if stat.l1_cnt > 0 else 0,
                                "l1_ant_avg": stat.l1_ant_avg / stat.l1_cnt if stat.l1_cnt > 0 else 0,
                                "l1_ulc_prb_hist": list(stat.l1_ulc_prb_hist),
                                "l1_ulc_mcs_hist": list(stat.l1_ulc_mcs_hist),
                                "l1_ulc_tbs_hist": list(stat.l1_ulc_tbs_hist),
                                "l1_ulc_ant_hist": list(stat.l1_ulc_ant_hist)
                            }

                            if uectx is None:
                                s["rnti"] = stat.rnti
                                                    
                            output["ues"].append(s)   

                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                    if len(output["ues"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == FAPI_CRC_STATS_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__fapi_crc_stats)
                    )
                    data = data_ptr.contents
                    stats = list(data.stats)
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "FAPI_CRC_STATS",
                        "ues": []
                    }
                    cnt = 0
                    for stat in stats:
                        if stat.rnti > 0:
                            ueid = state.ue_map.getid_by_pci_rnti(stat.cell_id, stat.rnti)                    
                            uectx = state.ue_map.getuectx(ueid)
                            s = {
                                "cell_id": stat.cell_id,
                                "ueid": ueid,
                                "ue_ctx": None if uectx is None else uectx.concise_dict(),
                                "l1_crc_ta_hist": list(stat.l1_crc_ta_hist),
                                "l1_crc_snr_hist": list(stat.l1_crc_snr_hist),
                                "l1_ta_min": stat.l1_ta_min,
                                "l1_ta_max": stat.l1_ta_max,
                                "l1_snr_min": stat.l1_snr_min,
                                "l1_snr_max": stat.l1_snr_max
                            }

                            if uectx is None:
                                s["rnti"] = stat.rnti
                                                    
                            output["ues"].append(s)   

                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                    if len(output["ues"]) > 0:
                        state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

                elif stream_idx == FAPI_RACH_STATS_SIDX:
                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__rach_stats)
                    )
                    data = data_ptr.contents
                    output = {
                        "timestamp": data.timestamp,
                        "stream_index": "FAPI_RACH_STATS",
                        "ta": [],
                        "pwr": []
                    }
                    stats = list(data.l1_rach_ta_hist)
                    cnt = 0
                    for stat in stats:
                        output["ta"].append({
                            "ta": stat.ta,
                            "cnt": stat.cnt,
                        })
                        cnt += 1
                        if cnt >= data.l1_rach_ta_hist_count:
                            break
                    stats = list(data.l1_rach_pwr_hist)
                    cnt = 0
                    for stat in stats:
                        output["pwr"].append({
                            "pwr": stat.pwr,
                            "cnt": stat.cnt
                        })
                        cnt += 1
                        if cnt >= data.l1_rach_pwr_hist_count:
                            break
                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")


                ###########
                # XRAN
                
                elif stream_idx == XRAN_CODELET_OUT_SIDX:

                    data_ptr = ctypes.cast(
                        data_entry.data, ctypes.POINTER(struct__packet_stats)
                    )

                    data = data_ptr.contents
                    ul_data_stats = data.ul_packet_stats.data_packet_stats
                    dl_data_stats = data.dl_packet_stats.data_packet_stats
                    dl_control_stats = data.dl_packet_stats.ctrl_packet_stats

                    state.logger.log_msg(log_enabled, rlog_enabled, "", "****----------------------------")
                    state.logger.log_msg(log_enabled, rlog_enabled, "", f"*Hi App 1: timestamp: {data.timestamp}")
                    state.logger.log_msg(log_enabled, rlog_enabled, "", f"*DL Ctl: {dl_control_stats.Packet_count} {list(dl_control_stats.packet_inter_arrival_info.hist)}")
                    state.logger.log_msg(log_enabled, rlog_enabled, "", f"*DL Data: {dl_data_stats.Packet_count} {dl_data_stats.Prb_count} {list(dl_data_stats.packet_inter_arrival_info.hist)}")


                else:
                    state.logger.log_msg(True, False, "", f"Unknown stream index: {stream_idx}")
                    output = {
                        "stream_index": stream_idx,
                        "error": "Unknown stream index"
                    }

                    # Send the output to the dashboard
                    state.logger.log_msg(log_enabled, rlog_enabled, "Dashboard", f"{json.dumps(output)}")

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
    print(f"Starting JRTC Dashboard app for device: {device}", flush=True)

    global UECTX_DU_ADD_SIDX
    global UECTX_DU_UPDATE_CRNTI_SIDX
    global UECTX_DU_DEL_SIDX
    global UECTX_CUCP_ADD_SIDX
    global UECTX_CUCP_UPDATE_CRNTI_SIDX 
    global UECTX_CUCP_DEL_SIDX
    global UECTX_CUCP_E1AP_BEARER_SETUP_SIDX 
    global UECTX_CUUP_E1AP_BEARER_SETUP_SIDX
    global UECTX_CUUP_E1AP_BEARER_DEL_SIDX
    global MAC_SCHED_CRC_STATS_SIDX
    global MAC_SCHED_BSR_STATS_SIDX
    global MAC_SCHED_PHR_STATS_SIDX
    global MAC_SCHED_UCI_STATS_SIDX
    global MAC_SCHED_DL_HARQ_SIDX
    global MAC_SCHED_UL_HARQ_SIDX
    global RLC_DL_STATS_SIDX
    global RLC_UL_STATS_SIDX
    global PDCP_DL_STATS_SIDX
    global PDCP_UL_STATS_SIDX
    global RRC_UE_ADD_SIDX
    global RRC_UE_PROCEDURE_SIDX
    global RRC_UE_REMOVE_SIDX
    global RRC_UE_UPDATE_CONTEXT_SIDX
    global RRC_UE_UPDATE_ID_SIDX 
    global NGAP_PROCEDURE_STARTED_SIDX
    global NGAP_PROCEDURE_COMPLETED_SIDX
    global NGAP_RESET_SIDX
    global FAPI_DL_CONFIG_SIDX 
    global FAPI_UL_CONFIG_SIDX 
    global FAPI_CRC_STATS_SIDX 
    global FAPI_RACH_STATS_SIDX 
    global JBPF_STATS_REPORT_SIDX
    global XRAN_CODELET_OUT_SIDX
    global rlog_enabled
    global log_enabled


    UECTX_DU_ADD_SIDX = -1
    UECTX_DU_UPDATE_CRNTI_SIDX = -1
    UECTX_DU_DEL_SIDX = -1
    UECTX_CUCP_ADD_SIDX = -1
    UECTX_CUCP_UPDATE_CRNTI_SIDX = -1
    UECTX_CUCP_DEL_SIDX = -1
    UECTX_CUCP_E1AP_BEARER_SETUP_SIDX = -1
    UECTX_CUUP_E1AP_BEARER_SETUP_SIDX = -1
    UECTX_CUUP_E1AP_BEARER_DEL_SIDX = -1
    MAC_SCHED_CRC_STATS_SIDX = -1
    MAC_SCHED_BSR_STATS_SIDX = -1
    MAC_SCHED_PHR_STATS_SIDX = -1
    MAC_SCHED_UCI_STATS_SIDX = -1
    MAC_SCHED_DL_HARQ_SIDX = -1
    MAC_SCHED_UL_HARQ_SIDX = -1
    RLC_DL_STATS_SIDX = -1
    RLC_UL_STATS_SIDX = -1
    PDCP_DL_STATS_SIDX = -1
    PDCP_UL_STATS_SIDX = -1
    RRC_UE_ADD_SIDX = -1
    RRC_UE_PROCEDURE_SIDX = -1
    RRC_UE_REMOVE_SIDX = -1
    RRC_UE_UPDATE_CONTEXT_SIDX = -1
    RRC_UE_UPDATE_ID_SIDX = -1
    NGAP_PROCEDURE_STARTED_SIDX = -1
    NGAP_PROCEDURE_COMPLETED_SIDX = -1
    NGAP_RESET_SIDX = -1
    FAPI_DL_CONFIG_SIDX = -1
    FAPI_UL_CONFIG_SIDX = -1
    FAPI_CRC_STATS_SIDX = -1
    FAPI_RACH_STATS_SIDX = -1
    JBPF_STATS_REPORT_SIDX = -1
    XRAN_CODELET_OUT_SIDX = -1

    last_cnt = 0

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
                "jrtc_dashboard",  # Log type
                la_workspace_id,         
                la_primary_key,         
                params.la_msgs_per_batch,
                params.la_bytes_per_batch,
                params.la_tx_timeout_secs,
                params.la_stats_period_secs
            ), 
            dbg=False
        )

    stream_id = "dashboard"
    stream_type = "dashboard"

    hostname = os.environ.get("HOSTNAME", "")

    # Initialize the app
    state = AppStateVars(
        logger=Logger(device, hostname, stream_id, stream_type, remote_logger=la_logger),
        ue_map=UeContextsMap(dbg=False) if params.include_ue_contexts else None, 
        app=None,
        device=device)

    # if LA is configured and intitialised, send to LA, and not write to console.
    # else, write to console
    rlog_enabled = (la_logger is not None)
    log_enabled = (not rlog_enabled)
    

    #####################################################
    ### UE contexts

    if params.include_ue_contexts:

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/du_ue_ctx_creation", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_DU_ADD_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_DU_ADD_SIDX: {UECTX_DU_ADD_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/du_ue_ctx_update_crnti", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_DU_UPDATE_CRNTI_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_DU_UPDATE_CRNTI_SIDX: {UECTX_DU_UPDATE_CRNTI_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/du_ue_ctx_deletion", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_DU_DEL_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_DU_DEL_SIDX: {UECTX_DU_DEL_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/cucp_uemgr_ue_add", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUCP_ADD_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUCP_ADD_SIDX: {UECTX_CUCP_ADD_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/cucp_uemgr_ue_update", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUCP_UPDATE_CRNTI_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUCP_UPDATE_CRNTI_SIDX: {UECTX_CUCP_UPDATE_CRNTI_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/cucp_uemgr_ue_remove", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUCP_DEL_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUCP_DEL_SIDX: {UECTX_CUCP_DEL_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/e1_cucp_bearer_context_setup", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUCP_E1AP_BEARER_SETUP_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUCP_E1AP_BEARER_SETUP_SIDX: {UECTX_CUCP_E1AP_BEARER_SETUP_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/e1_cuup_bearer_context_setup", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUUP_E1AP_BEARER_SETUP_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUUP_E1AP_BEARER_SETUP_SIDX: {UECTX_CUUP_E1AP_BEARER_SETUP_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/e1_cuup_bearer_context_release", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUUP_E1AP_BEARER_DEL_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUUP_E1AP_BEARER_DEL_SIDX: {UECTX_CUUP_E1AP_BEARER_DEL_SIDX}")
        last_cnt += 1



    #####################################################
    ### Perf

    if params.include_perf:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/jbpf_stats/jbpf_stats_report", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        JBPF_STATS_REPORT_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"JBPF_STATS_REPORT_SIDX: {JBPF_STATS_REPORT_SIDX}")
        last_cnt += 1



    #####################################################
    ### RRC

    if params.include_rrc:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_add", 
                b"rrc_ue_add_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RRC_UE_ADD_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"RRC_UE_ADD_SIDX: {RRC_UE_ADD_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_procedure", 
                b"rrc_ue_procedure_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RRC_UE_PROCEDURE_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"RRC_UE_PROCEDURE_SIDX: {RRC_UE_PROCEDURE_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_remove", 
                b"rrc_ue_remove_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RRC_UE_REMOVE_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"RRC_UE_REMOVE_SIDX: {RRC_UE_REMOVE_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_update_context", 
                b"rrc_ue_update_context_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RRC_UE_UPDATE_CONTEXT_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"RRC_UE_UPDATE_CONTEXT_SIDX: {RRC_UE_UPDATE_CONTEXT_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_update_id", 
                b"rrc_ue_update_id_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RRC_UE_UPDATE_ID_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"RRC_UE_UPDATE_ID_SIDX: {RRC_UE_UPDATE_ID_SIDX}")
        last_cnt += 1



    #####################################################
    ### NGAP

    if params.include_ngap:
    
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ngap/ngap_procedure_started", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        NGAP_PROCEDURE_STARTED_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"NGAP_PROCEDURE_STARTED_SIDX: {NGAP_PROCEDURE_STARTED_SIDX}")
        last_cnt += 1    

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ngap/ngap_procedure_completed", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        NGAP_PROCEDURE_COMPLETED_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"NGAP_PROCEDURE_COMPLETED_SIDX: {NGAP_PROCEDURE_COMPLETED_SIDX}")
        last_cnt += 1    

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ngap/ngap_reset", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        NGAP_RESET_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"NGAP_RESET_SIDX: {NGAP_RESET_SIDX}")
        last_cnt += 1



    #####################################################
    ### RLC

    if params.include_rlc:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rlc_stats/rlc_collect", 
                b"output_map_dl"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RLC_DL_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"RLC_DL_STATS_SIDX: {RLC_DL_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rlc_stats/rlc_collect", 
                b"output_map_ul"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RLC_UL_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"RLC_UL_STATS_SIDX: {RLC_UL_STATS_SIDX}")
        last_cnt += 1
        
    
    
    #####################################################
    ### PDCP

    if params.include_pdcp:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/pdcp_stats/pdcp_collect", 
                b"output_map_dl"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        PDCP_DL_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"PDCP_DL_STATS_SIDX: {PDCP_DL_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/pdcp_stats/pdcp_collect", 
                b"output_map_ul"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        PDCP_UL_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"PDCP_UL_STATS_SIDX: {PDCP_UL_STATS_SIDX}")
        last_cnt += 1



    #####################################################
    ### MAC

    if params.include_mac:
        # MAC SCHEDULER
        streams.append(JrtcStreamCfg_t(
                JrtcStreamIdCfg_t(
                    JRTC_ROUTER_REQ_DEST_ANY, 
                    JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                    b"dashboard://jbpf_agent/mac_stats/mac_stats_collect", 
                    b"output_map_crc"),
                True,   # is_rx
                None    # No AppChannelCfg 
            ))
        MAC_SCHED_CRC_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"MAC_SCHED_CRC_STATS_SIDX: {MAC_SCHED_CRC_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
                JrtcStreamIdCfg_t(
                    JRTC_ROUTER_REQ_DEST_ANY, 
                    JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                    b"dashboard://jbpf_agent/mac_stats/mac_stats_collect", 
                    b"output_map_bsr"),
                True,   # is_rx
                None    # No AppChannelCfg 
            ))
        MAC_SCHED_BSR_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"MAC_SCHED_BSR_STATS_SIDX: {MAC_SCHED_BSR_STATS_SIDX}")
        last_cnt += 1
        
        streams.append(JrtcStreamCfg_t(
                JrtcStreamIdCfg_t(
                    JRTC_ROUTER_REQ_DEST_ANY, 
                    JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                    b"dashboard://jbpf_agent/mac_stats/mac_stats_collect", 
                    b"output_map_phr"),
                True,   # is_rx
                None    # No AppChannelCfg 
            ))
        MAC_SCHED_PHR_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"MAC_SCHED_PHR_STATS_SIDX: {MAC_SCHED_PHR_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
                JrtcStreamIdCfg_t(
                    JRTC_ROUTER_REQ_DEST_ANY, 
                    JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                    b"dashboard://jbpf_agent/mac_stats/mac_stats_collect", 
                    b"output_map_uci"),
                True,   # is_rx
                None    # No AppChannelCfg 
            ))
        MAC_SCHED_UCI_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"MAC_SCHED_UCI_STATS_SIDX: {MAC_SCHED_UCI_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
                JrtcStreamIdCfg_t(
                    JRTC_ROUTER_REQ_DEST_ANY, 
                    JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                    b"dashboard://jbpf_agent/mac_stats/mac_stats_collect_harq", 
                    b"output_map_dl_harq"),
                True,   # is_rx
                None    # No AppChannelCfg 
            ))
        MAC_SCHED_DL_HARQ_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"MAC_SCHED_DL_HARQ_SIDX: {MAC_SCHED_DL_HARQ_SIDX}")
        last_cnt += 1


        streams.append(JrtcStreamCfg_t(
                JrtcStreamIdCfg_t(
                    JRTC_ROUTER_REQ_DEST_ANY, 
                    JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                    b"dashboard://jbpf_agent/mac_stats/mac_stats_collect_harq", 
                    b"output_map_ul_harq"),
                True,   # is_rx
                None    # No AppChannelCfg 
            ))
        MAC_SCHED_UL_HARQ_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"MAC_SCHED_UL_HARQ_SIDX: {MAC_SCHED_UL_HARQ_SIDX}")
        last_cnt += 1


    #####################################################
    ### FAPI

    if params.include_fapi:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_dl_config_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        FAPI_DL_CONFIG_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"FAPI_DL_CONFIG_SIDX: {FAPI_DL_CONFIG_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_ul_config_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        FAPI_UL_CONFIG_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"FAPI_UL_CONFIG_SIDX: {FAPI_UL_CONFIG_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_crc_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        FAPI_CRC_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"FAPI_CRC_STATS_SIDX: {FAPI_CRC_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_rach_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        FAPI_RACH_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"FAPI_RACH_STATS_SIDX: {FAPI_RACH_STATS_SIDX}")
        last_cnt += 1


    #####################################################
    ### XRAN

    if params.include_xran:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/xran_packets/reporter", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        XRAN_CODELET_OUT_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"XRAN_CODELET_OUT_SIDX: {XRAN_CODELET_OUT_SIDX}")
        last_cnt += 1

    app_cfg = JrtcAppCfg_t(
        b"dashboard",                                  # context
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

