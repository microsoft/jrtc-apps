- [1. Introduction](#1-introduction)
- [2. UE Context Identifiers](#2-ue-context-identifiers)
  - [2.1. du\_ue\_ctx\_creation](#21-du_ue_ctx_creation)
  - [2.2. du\_ue\_ctx\_update\_crnti](#22-du_ue_ctx_update_crnti)
  - [2.3. du\_ue\_ctx\_deletion](#23-du_ue_ctx_deletion)
  - [2.4. cucp\_uemgr\_ue\_add](#24-cucp_uemgr_ue_add)
  - [2.5. cucp\_uemgr\_ue\_update](#25-cucp_uemgr_ue_update)
  - [2.6. cucp\_uemgr\_ue\_remove](#26-cucp_uemgr_ue_remove)
  - [2.7. e1\_cucp\_bearer\_context\_setup](#27-e1_cucp_bearer_context_setup)
  - [2.8. e1\_cuup\_bearer\_context\_setup](#28-e1_cuup_bearer_context_setup)
  - [2.9. e1\_cuup\_bearer\_context\_release](#29-e1_cuup_bearer_context_release)
- [3. RRC](#3-rrc)
  - [3.1. rrc\_ue\_add](#31-rrc_ue_add)
  - [3.2. rrc\_ue\_remove](#32-rrc_ue_remove)
  - [3.3. rrc\_ue\_update\_context](#33-rrc_ue_update_context)
  - [3.4. rrc\_ue\_update\_id](#34-rrc_ue_update_id)
  - [3.5. rrc\_ue\_procedure](#35-rrc_ue_procedure)
- [4. NGAP](#4-ngap)
  - [4.1. ngap\_procedure\_started](#41-ngap_procedure_started)
  - [4.2. ngap\_procedure\_completed](#42-ngap_procedure_completed)
  - [4.3. ngap\_reset](#43-ngap_reset)
- [5. PDCP](#5-pdcp)
  - [5.1. pdcp\_dl\_new\_sdu](#51-pdcp_dl_new_sdu)
  - [5.2. pdcp\_dl\_tx\_data\_pdu](#52-pdcp_dl_tx_data_pdu)
  - [5.3. pdcp\_dl\_tx\_control\_pdu](#53-pdcp_dl_tx_control_pdu)
  - [5.4. pdcp\_dl\_discard](#54-pdcp_dl_discard)
  - [5.5. pdcp\_dl\_deletion](#55-pdcp_dl_deletion)
  - [5.6. pdcp\_ul\_deliver\_sdu](#56-pdcp_ul_deliver_sdu)
  - [5.7. pdcp\_ul\_deliver\_sdu](#57-pdcp_ul_deliver_sdu)
  - [5.8. pdcp\_ul\_rx\_data\_pdu](#58-pdcp_ul_rx_data_pdu)
  - [5.9. pdcp\_ul\_rx\_control\_pdu](#59-pdcp_ul_rx_control_pdu)
  - [5.10. pdcp\_ul\_deletion](#510-pdcp_ul_deletion)
  - [5.11. pdcp\_collect](#511-pdcp_collect)
    - [5.11.1. Downlink statistics](#5111-downlink-statistics)
    - [5.11.2. Uplink statistics](#5112-uplink-statistics)
- [6. RLC](#6-rlc)
  - [6.1. rlc\_dl\_new\_sdu](#61-rlc_dl_new_sdu)
  - [6.2. rlc\_dl\_tx\_pdu](#62-rlc_dl_tx_pdu)
  - [6.3. rlc\_dl\_tx\_sdu\_started](#63-rlc_dl_tx_sdu_started)
  - [6.4. rlc\_dl\_tx\_sdu\_completed](#64-rlc_dl_tx_sdu_completed)
  - [6.5. rlc\_dl\_tx\_sdu\_delivered](#65-rlc_dl_tx_sdu_delivered)
  - [6.6. rlc\_dl\_am\_tx\_pdu\_retx\_count](#66-rlc_dl_am_tx_pdu_retx_count)
  - [6.7. rlc\_dl\_am\_tx\_pdu\_retx\_max\_reached](#67-rlc_dl_am_tx_pdu_retx_max_reached)
  - [6.8. rlc\_dl\_deletion](#68-rlc_dl_deletion)
  - [6.9. rlc\_ul\_rx\_pdu](#69-rlc_ul_rx_pdu)
  - [6.10. rlc\_ul\_deliver\_sdu](#610-rlc_ul_deliver_sdu)
  - [6.11. rlc\_ul\_deletion](#611-rlc_ul_deletion)
  - [6.12. rlc\_collect](#612-rlc_collect)
    - [6.12.1. Downlink statistics](#6121-downlink-statistics)
    - [6.12.2. Uplink statistics](#6122-uplink-statistics)
- [7. MAC](#7-mac)
  - [7.1. mac\_sched\_bsr\_stats](#71-mac_sched_bsr_stats)
  - [7.2. mac\_sched\_crc\_stats](#72-mac_sched_crc_stats)
  - [7.3. mac\_sched\_phr\_stats](#73-mac_sched_phr_stats)
  - [7.4. mac\_sched\_uci\_pdu\_stats](#74-mac_sched_uci_pdu_stats)
  - [7.5. mac\_sched\_ue\_deletion](#75-mac_sched_ue_deletion)
  - [7.6. mac\_stats\_collect](#76-mac_stats_collect)
- [8. FAPI](#8-fapi)
  - [8.1. FAPI DL Configuration](#81-fapi-dl-configuration)
    - [8.1.1. fapi\_gnb\_dl\_config\_stats\_collect](#811-fapi_gnb_dl_config_stats_collect)
    - [8.1.2. fapi\_gnb\_dl\_config\_stats\_report](#812-fapi_gnb_dl_config_stats_report)
  - [8.2. FAPI UL Configuration](#82-fapi-ul-configuration)
    - [8.2.1. fapi\_gnb\_ul\_config\_stats\_collect](#821-fapi_gnb_ul_config_stats_collect)
    - [8.2.2. fapi\_gnb\_ul\_config\_stats\_report](#822-fapi_gnb_ul_config_stats_report)
  - [8.3. FAPI UL CRC](#83-fapi-ul-crc)
    - [8.3.1. fapi\_gnb\_crc\_stats\_collect](#831-fapi_gnb_crc_stats_collect)
    - [8.3.2. fapi\_gnb\_crc\_stats\_report](#832-fapi_gnb_crc_stats_report)
  - [8.4. FAPI UL RACH](#84-fapi-ul-rach)
    - [8.4.1. fapi\_gnb\_rach\_stats\_collect](#841-fapi_gnb_rach_stats_collect)
    - [8.4.2. fapi\_gnb\_rach\_stats\_report](#842-fapi_gnb_rach_stats_report)
- [9. XRAN Packets](#9-xran-packets)
  - [9.1. xran\_packets\_collect](#91-xran_packets_collect)
  - [9.2. xran\_packets\_report](#92-xran_packets_report)
- [10. Slice management](#10-slice-management)
  - [10.1. slice\_management](#101-slice_management)
- [11. Performance statistics](#11-performance-statistics)
  - [11.1. jbpf\_stats\_report](#111-jbpf_stats_report)


# 1. Introduction

Numerous Jbpf codelets have been developed.
The general behaviour of these are described below.

# 2. UE Context Identifiers

These codelets expose the various UE identifiers used across different layers of the stack. For example, the DU, CU-CP, and CU-UP each maintain a separate "ue_index" to identify UE contexts within their respective domains. These indices are managed independently, meaning that "ue_index=<n>" in the DU may refer to a different UE than "ue_index=<n>" in the CU-CP or CU-UP.

In addition to ue_index, other identifiers such as PLMN, PCI, C-RNTI, e1ap_cucp_ue_index, and e1ap_cuup_ue_e1ap_id are also exposed.

The codelets themselves do not perform any aggregation or statistical analysis—they simply pass this information to higher-layer components, such as the [dashboard](./example_dashboard.md) application. These components are responsible for correlating the various identifiers across different entities.

There is a single .proto file used by all of the codelets, file [codelets/ue_contexts/ue_contexts.proto](../codelets/ue_contexts/ue_contexts.proto)

The following is a brief description of each codelet.

## 2.1. [du_ue_ctx_creation](../codelets/ue_contexts/du_ue_ctx_creation.cpp)
Binds to hook [__du_ue_ctx_creation__](srsran_hooks.md#41-du_ue_ctx_creation).   

It exposes the following identifiers: du_ue_index, TAC, PLMN, NCI, PCI, and C-RNTI.

## 2.2. [du_ue_ctx_update_crnti](../codelets/ue_contexts/du_ue_ctx_update_crnti.cpp)
Binds to hook [__du_ue_ctx_update_crnti__](srsran_hooks.md#42-du_ue_ctx_update_crnti).

The du_ue_index is used as the key to identify the context.

## 2.3. [du_ue_ctx_deletion](../codelets/ue_contexts/du_ue_ctx_deletion.cpp)
Binds to hook [__du_ue_ctx_deletion__](srsran_hooks.md#43-du_ue_ctx_deletion).  

Invoked when a UE context is deleted in the DU.  The du_ue_index is used as the key to identify the context.

## 2.4. [cucp_uemgr_ue_add](../codelets/ue_contexts/cucp_uemgr_ue_add.cpp)
Binds to hook [__cucp_uemgr_ue_add__](srsran_hooks.md#81-cucp_uemgr_ue_add).  

It exposes the following identifiers: cucp_ue_index, PLMN, PCI, and C-RNTI.
Higher-layer components can use the tuple (PLMN, PCI, C-RNTI) to correlate this context with the data exposed by __du_ue_ctx_creation__.

## 2.5. [cucp_uemgr_ue_update](../codelets/ue_contexts/cucp_uemgr_ue_update.cpp)
Binds to hook [__cucp_uemgr_ue_update__](srsran_hooks.md#82-cucp_uemgr_ue_update).  

The cucp_ue_index is used as the key to identify the context.

## 2.6. [cucp_uemgr_ue_remove](../codelets/ue_contexts/cucp_uemgr_ue_remove.cpp)
Binds to hook [__cucp_uemgr_ue_remove__](srsran_hooks.md#83-cucp_uemgr_ue_remove).  

The cucp_ue_index is used as the key to identify the context.
Higher-layer components can use this event to clean up or disassociate any previously correlated data tied to this context.

## 2.7. [e1_cucp_bearer_context_setup](../codelets/ue_contexts/e1_cucp_bearer_context_setup.cpp)
Binds to hook [__e1_cucp_bearer_context_setup__](srsran_hooks.md#711-e1_cucp_bearer_context_setup).  

It uses the cucp_ue_index to identify the UE context, and exposes the cucp_ue_e1ap_id.

## 2.8. [e1_cuup_bearer_context_setup](../codelets/ue_contexts/e1_cuup_bearer_context_setup.cpp)
Binds to hook [__e1_cuup_bearer_context_setup__](srsran_hooks.md#721-e1_cuup_bearer_context_setup).  

It exposes the cuup_ue_index, the success status of the setup, and the associated E1AP identifiers: cucp_ue_e1ap_id and cuup_ue_e1ap_id.
The cucp_ue_e1ap_id can be used as a field to correlate with the information exposed by __e1_cucp_bearer_context_setup__.

## 2.9. [e1_cuup_bearer_context_release](../codelets/ue_contexts/e1_cuup_bearer_context_release.cpp)
Binds to hook [__e1_cuup_bearer_context_release__](srsran_hooks.md#723-e1_cuup_bearer_context_release).  

It uses the cuup_ue_index to identify the UE context, the success status of the release, and the E1AP identifiers: cucp_ue_e1ap_id and cuup_ue_e1ap_id.
This event signals the teardown of a previously established bearer context in the CU-UP.

# 3. RRC

These codelets expose the various events which occur at the RRC layer.

## 3.1. [rrc_ue_add](../codelets/rrc/rrc_ue_add.cpp)
Binds to hook [rrc_ue_add](srsran_hooks.md#101-rrc_ue_add).

Output is defined in [rrc_ue_add.proto](../codelets/rrc/rrc_ue_add.proto).

Exposes  cucp_ue_index, CRNTI, PCI, TAC, PLMN, NCI

## 3.2. [rrc_ue_remove](../codelets/rrc/rrc_ue_remove.cpp)
Binds to hook [rrc_ue_remove](srsran_hooks.md#104-rrc_ue_remove).

Output is defined in [rrc_ue_remove.proto](../codelets/rrc/rrc_ue_remove.proto).

The cucp_ue_index is used as the key to identify the context.

## 3.3. [rrc_ue_update_context](../codelets/rrc/rrc_ue_update_context.cpp)
Binds to hook [rrc_ue_update_context](srsran_hooks.md#102-rrc_ue_update_context).

Output is defined in [rrc_ue_update_context.proto](../codelets/rrc/rrc_ue_update_context.proto).

The cucp_ue_index is used as the key to identify the context.  Exposes UEs identitiesr whuch are being updated.

## 3.4. [rrc_ue_update_id](../codelets/rrc/rrc_ue_update_id.cpp)
Binds to hook [rrc_ue_update_id](srsran_hooks.md#103-rrc_ue_update_id).

Output is defined in [rrc_ue_update_id.proto](../codelets/rrc/rrc_ue_update_id.proto).

The cucp_ue_index is used as the key to identify the context.  Exposes the updated TMSI.


## 3.5. [rrc_ue_procedure](../codelets/rrc/rrc_ue_procedure.cpp)
Binds to hook [rrc_ue_procedure_completed](srsran_hooks.md#106-rrc_ue_procedure_completed).

Output is defined in [rrc_ue_procedure.proto](../codelets/rrc/rrc_ue_procedure.proto).

The cucp_ue_index is used as the key to identify the context.  Indicates what RRC procedure has been execued, and whether it is successful.


# 4. NGAP

These codelets expose the various events which occur at the NGAP layer.  They also expose identifiers such as the __ngap_ran_ue_id__ and __ngap_amf_ue_id__.

The outputs of various codelers is defined in [ngap.proto](../codelets/ngap/ngap.proto).

## 4.1. [ngap_procedure_started](../codelets/ngap/ngap_procedure_started.cpp)
Binds to hook [ngap_procedure_started](srsran_hooks.md#91-ngap_procedure_started).

Invoked when an NGAP procedure starts.  The __cucp_ue_index__and __ran_ue_ngap_id__ are exposed.


## 4.2. [ngap_procedure_completed](../codelets/ngap/ngap_procedure_completed.cpp)
Binds to hook [ngap_procedure_completed](srsran_hooks.md#92-ngap_procedure_completed).

Invoked when an NGAP procedure starts.  The __cucp_ue_index__, __ran_ue_ngap_id__ and __amf_ue_ngap_id__ are exposed.

Higher-layer components, such as the [dashboard](./example_dashboard.md) application, can use NGAP information in conjunction with core data to correlate RAN identifiers (e.g., du_index, cucp_index, etc.) with core identifiers (e.g., SUCI, SUPI) for individual UEs.


## 4.3. [ngap_reset](../codelets/ngap/ngap_reset.cpp)
Binds to hook [ngap_procedure_reset](srsran_hooks.md#93-ngap_procedure_reset).

This is invoked when a NGAP Reset occurs.  In the cases where individual UEs are being reset, the identifiers __ran_ue_id__ and __amf_ue_id__ will be present.   If the NGAP Reset is for the whole interface, these identifiers will not be set.


# 5. PDCP

There are a number of codelets associated with the PDCP layer. These include:

- pdcp_dl...: These codelets are responsible for collecting downlink statistics such as latencies, queue sizes, and throughput rates.

- pdcp_ul...: These codelets gather uplink statistics, including queue sizes and throughput rates.

- pdcp_collect: This is the only PDCP codelet that sends data to higher-layer components. It consolidates and transmits the downlink and uplink statistics collected by the other PDCP codelets. The PDCP downlink and uplink codelets solely perform data collection and do not transmit information directly.


## 5.1. [pdcp_dl_new_sdu](../codelets/pdcp/pdcp_dl_new_sdu.cpp)
Binds to hook [pdcp_dl_new_sdu](srsran_hooks.md#613-pdcp_dl_new_sdu).


## 5.2. [pdcp_dl_tx_data_pdu](../codelets/pdcp/pdcp_dl_tx_data_pdu.cpp)
Binds to hook [pdcp_dl_tx_data_pdu](srsran_hooks.md#614-pdcp_dl_tx_data_pdu).


## 5.3. [pdcp_dl_tx_control_pdu](../codelets/pdcp/pdcp_dl_tx_control_pdu.cpp)
Binds to hook [pdcp_dl_tx_control_pdu](srsran_hooks.md#615-pdcp_dl_tx_control_pdu).


## 5.4. [pdcp_dl_discard](../codelets/pdcp/pdcp_dl_discard.cpp) 
Binds to hook [pdcp_dl_discard_pdu](srsran_hooks.md#618-pdcp_dl_discard_pdu).


## 5.5. [pdcp_dl_deletion](../codelets/pdcp/pdcp_dl_deletion.cpp)
Binds to hook [pdcp_dl_deletion](srsran_hooks.md#612-pdcp_dl_deletion).


## 5.6. [pdcp_ul_deliver_sdu](../codelets/pdcp/pdcp_ul_deliver_sdu.cpp)
Binds to hook [pdcp_ul_deliver_sdu](srsran_hooks.md#625-pdcp_ul_deliver_sdu).


## 5.7. [pdcp_ul_deliver_sdu](../codelets/pdcp/pdcp_ul_deliver_sdu.cpp)
Binds to hook [pdcp_ul_rx_data_pdu](srsran_hooks.md#623-pdcp_ul_rx_data_pdu).


## 5.8. [pdcp_ul_rx_data_pdu](../codelets/pdcp/pdcp_ul_rx_data_pdu.cpp)
Binds to hook [pdcp_ul_rx_data_pdu](srsran_hooks.md#623-pdcp_ul_rx_data_pdu).


## 5.9. [pdcp_ul_rx_control_pdu](../codelets/pdcp/pdcp_ul_rx_control_pdu.cpp)
Binds to hook [pdcp_ul_rx_control_pdu](srsran_hooks.md##624-pdcp_ul_rx_control_pdu).


## 5.10. [pdcp_ul_deletion](../codelets/pdcp/pdcp_ul_deletion.cpp)
Binds to hook [pdcp_ul_deletion](srsran_hooks.md#22-pdcp_ul_deletion).


## 5.11. [pdcp_collect](../codelets/pdcp/pdcp_collect.cpp) 
Binds to hook [report_stats](srsran_hooks.md#121-report_stats).  

This is the codelet which sends the PDCP statistics to the higher layers.

These are described in the following sections.

Note that for the statistics, __cu_ue_index__ is used to identiofy the context.  If __is_srb=True__, this represents the __cucp_ue_index__, otherwise it represents the __cuup_ue_index__.

### 5.11.1. Downlink statistics

These are the downlink statistics.

The output is defined in [pdcp_dl_stats.proto](../codelets/pdcp/pdcp_dl_stats.proto).

__sdu_new_bytes__:  the number of SDU bytes received at the north interface (SDAP).

__sdu_discarded__:  the number of discarded SDUs arriving from SDAP.

__data_pdu_tx_bytes__:  Number of DATA PDU bytes transmitted to RLC.

__data_pdu_retx_bytes__:  Number of DATA PDU bytes retransmitted to RLC.

__control_pdu_tx_bytes__: Number of CONTROL PDU bytes transmitted to RLC.

__pdu_window_pkts__: min/avg/max stats for the number of packets in the transmission buffer (queue).
This is sampled in every PDCP hook. 

__pdu_window_bytes__: min/avg/max stats for the number of bytes in the transmission buffer (queue)
This is sampled in every PDCP hook. 

__sdu_tx_latency__:  min/avg/max stats for tx latency (in nanosecs).  This is the time from when the SDU arrives from the higher layers (SDAP), to when is is transmitted to RLC.

### 5.11.2. Uplink statistics

These are the uplink statistics.

The output is defined in [pdcp_ul_stats.proto](../codelets/pdcp/pdcp_ul_stats.proto).

__rx_data_pdu_bytes__: Number of DATA PDU bytes received from RLC.

__rx_control_pdu_bytes__: Number of CONTROL PDU bytes received from RLC.

__sdu_delivered_bytes__:  the number of SDU bytes delivered to the north interface (SDAP).

__pdu_window_pkts__: min/avg/max stats for the number of packets in the reception buffer (to be delivered to SDAP). This is sampled in every PDCP hook. 

__pdu_window_bytes__: min/avg/max stats for the number of bytes in the reception buffer (to be delivered to SDAP). This is sampled in every PDCP hook. 



# 6. RLC

There are a number of codelets associated with the RLC layer. These include:

- rlc_dl...: These codelets are responsible for collecting downlink statistics such as window sizes, throughput rates and retransmission cpounts (AM only).

- rlc_ul...: These codelets gather uplink statistics, including window sizes and throughput rates.

- rlc_collect: This is the only RLC codelet that sends data to higher-layer components. It consolidates and transmits the downlink and uplink statistics collected by the other RLC codelets. The RLC downlink and uplink codelets solely perform data collection and do not transmit information directly.


## 6.1. [rlc_dl_new_sdu](../codelets/rlc/rlc_dl_new_sdu.cpp)
Binds to hook [rlc_dl_new_sdu](srsran_hooks.md#1113-rlc_dl_new_sdu).

## 6.2. [rlc_dl_tx_pdu](../codelets/rlc/rlc_dl_tx_pdu.cpp)
Binds to hook [rlc_dl_tx_pdu](srsran_hooks.md#1119-rlc_dl_tx_pdu).

## 6.3. [rlc_dl_tx_sdu_started](../codelets/rlc/rlc_dl_tx_sdu_started.cpp)
Binds to hook [rlc_dl_sdu_send_started](srsran_hooks.md#1116-rlc_dl_sdu_send_started).

## 6.4. [rlc_dl_tx_sdu_completed](../codelets/rlc/rlc_dl_tx_sdu_completed.cpp)
Binds to hook [rlc_dl_sdu_send_completed](srsran_hooks.md#1117-rlc_dl_sdu_send_completed).

## 6.5. [rlc_dl_tx_sdu_delivered](../codelets/rlc/rlc_dl_tx_sdu_delivered.cpp)
Binds to hook [rlc_dl_sdu_delivered](srsran_hooks.md#1118-rlc_dl_sdu_delivered).

## 6.6. [rlc_dl_am_tx_pdu_retx_count](../codelets/rlc/rlc_dl_am_tx_pdu_retx_count.cpp)
Binds to hook [rlc_dl_am_tx_pdu_retx_count](srsran_hooks.md#11111-rlc_dl_am_tx_pdu_retx_count).

## 6.7. [rlc_dl_am_tx_pdu_retx_max_reached](../codelets/rlc/rlc_dl_am_tx_pdu_retx_max_reached.cpp)
Binds to hook [rlc_dl_am_tx_pdu_max_retx_count_reached](srsran_hooks.md#11112-rlc_dl_am_tx_pdu_max_retx_count_reached).

## 6.8. [rlc_dl_deletion](../codelets/rlc/rlc_dl_deletion.cpp)  
Binds to hook [rlc_dl_deletion](srsran_hooks.md#1112-rlc_dl_deletion).

## 6.9. [rlc_ul_rx_pdu](../codelets/rlc/rlc_ul_rx_pdu.cpp)
Binds to hook [rlc_ul_rx_pdu](srsran_hooks.md#1123-rlc_ul_rx_pdu).

## 6.10. [rlc_ul_deliver_sdu](../codelets/rlc/rlc_ul_deliver_sdu.cpp)
Binds to hook [rlc_ul_sdu_delivered](srsran_hooks.md#1125-rlc_ul_sdu_delivered).

## 6.11. [rlc_ul_deletion](../codelets/rlc/rlc_ul_deletion.cpp) 
Binds to hook [rlc_ul_deletion](srsran_hooks.md#1122-rlc_ul_deletion).

## 6.12. [rlc_collect](../codelets/rlc/rlc_collect.cpp)             
Binds to hook [report_stats](srsran_hooks.md#121-report_stats).  

This is the codelet which sends the RLC statistics to the higher layers.

These are described in the following sections.

### 6.12.1. Downlink statistics

These are the downlink statistics.

The output is defined in [rlc_dl_stats.proto](../codelets/rlc/rlc_dl_stats.proto).

__sdu_queue_pkts__: min/avg/max stats for the number of packets in the SDU queue. 
This is a queue of packets coming from the PDCP and waiting to be sent. 
This is sampled in every RLC DL hook. 

__sdu_queue_bytes__: min/avg/max stats for the number of bytes in the SDU queue.
This is a queue of packets coming from the PDCP and waiting to be sent. 
This is sampled in every RLC DL hook. 

__sdu_new_bytes__:  the number of SDU bytes received from PDCP.

__pdu_tx_bytes__:  the number of DATA PDU bytes transmitted to MAC.

__sdu_tx_started__: min/avg/max stats for the "tx-started" latency.  This is the duration (in nanosecs) from the sdu-arrival time, to when the first byte of that SDU to transmitted to MAC. These will not be reported if no packets sent. 

__sdu_tx_completed__: min/avg/max stats for the "tx-completed" latency.  This is the duration (in nanosecs) from the sdu-arrival time, to when all of the bytes of that SDU to transmitted to MAC. These will not be reported if no packets sent.

__sdu_tx_delivered__: min/avg/max stats for the "tx-delivered" latency.  This is the duration (in nanosecs) from the sdu-arrival time, to when all of the bytes of that SDU have been received by the UE. These will not be reported if no packets sent.

The following are present just for AM mode:-

__pdu_retx_bytes__:  the number of DATA PDU bytes retransmitted to MAC.

__pdu_status_bytes__:  the number of STATUS PDU bytes transmitted to MAC.

__pdu_retx_count__: min/avg/max stats for the number of retx of a packet.

__pdu_window_pkts__: min/avg/max stats for the number of PDUs in the transmission buffer already sent to MAC, 
waiting to be acknowledged. A single PDU can carry multiple SDUs or their fragments. 
This is sampled in every RLC DL hook. 

__pdu_window_bytes__: min/avg/max stats for the number of PDU bytes in the transmission buffer already sent to MAC, 
waiting to be acknowledged. A single PDU can carry multiple SDUs or their fragments. 
This is sampled in every RLC DL hook. 


### 6.12.2. Uplink statistics

These are the uplink statistics.

The output is defined in [rlc_ul_stats.proto](../codelets/rlc/rlc_ul_stats.proto).

__pdu_bytes__:  the number of PDU bytes received from MAC.

__sdu_delivered_bytes__:  the number of SDU bytes delivered to PDCP.

__sdu_delivered_latency__: min/avg/max stats for the "rx-delivered" latency.  This is the duration (in nanosecs) from the time when the first byte of a PDU arrives, until the time when that SDU is delivered to PDCP.

The following is also present in UM and AM mode:

__pdu_window_pkts__: min/avg/max stats for the number of packets in the reception buffer.
This is sampled in every RLC UL hook. 


# 7. MAC


## 7.1. [mac_sched_bsr_stats](../codelets/mac/mac_sched_bsr_stats.cpp) 
Binds to hook [mac_sched_ul_bsr_indication](srsran_hooks.md#521-mac_sched_ul_bsr_indication).

Maintains statistics related to MAC Buffer Status Reports.

## 7.2. [mac_sched_crc_stats](../codelets/mac/mac_sched_crc_stats.cpp)
Binds to hook [mac_sched_crc_indication](srsran_hooks.md#522-mac_sched_crc_indication).

Maintains statistics related to MAC CRC results for received messages.

## 7.3. [mac_sched_phr_stats](../codelets/mac/mac_sched_phr_stats.cpp)
Binds to hook [mac_sched_ul_phr_indication](srsran_hooks.md#525-mac_sched_ul_phr_indication).

Maintains statistics related to MAC Power Headroom Reports.

## 7.4. [mac_sched_uci_pdu_stats](../codelets/mac/mac_sched_uci_pdu_stats.cpp)
Binds to hook [mac_sched_uci_indication](srsran_hooks.md#523-mac_sched_uci_indication).

Maintains statistics related to MAC UCI.  This includes HARQ, Timing-Advance-Offsets, RI, and CQI.

## 7.5. [mac_sched_ue_deletion](../codelets/mac/mac_sched_ue_deletion.cpp)
Binds to hook [mac_sched_ue_deletion](srsran_hooks.md#513-mac_sched_ue_deletion).

Invoked when a UE context is deleted at the MAC level.  

## 7.6. [mac_stats_collect](../codelets/mac/mac_stats_collect.cpp)
Binds to hook [report_stats](srsran_hooks.md#121-report_stats).  

This is the only MAC codelet that sends data to higher-layer components. It consolidates and transmits the BSR, CRC and PHR statistics collected by the other MAC codelets. 

It sends seperate messages as defined in:
The output is defined in [mac_sched_bsr_stats.proto](../codelets/mac/mac_sched_bsr_stats.proto).
The output is defined in [mac_sched_crc_stats.proto](../codelets/mac/mac_sched_crc_stats.proto).
The output is defined in [mac_sched_phr_stats.proto](../codelets/mac/mac_sched_phr_stats.proto).
The output is defined in [mac_sched_uci_stats.proto](../codelets/mac/mac_sched_uci_stats.proto).


# 8. FAPI

## 8.1. FAPI DL Configuration

### 8.1.1. [fapi_gnb_dl_config_stats_collect](../codelets/fapi_dl_conf/fapi_gnb_dl_config_stats_collect.cpp)
Binds to hook [fapi_dl_tti_request](srsran_hooks.md#321-fapi_dl_tti_request).

Collects statistics related to the FAPI Downlink Config Request messages.

### 8.1.2. [fapi_gnb_dl_config_stats_report](../codelets/fapi_dl_conf/fapi_gnb_dl_config_stats_report.cpp)
Binds to hook [report_stats](srsran_hooks.md#121-report_stats).  

Sends messages as defined in [fapi_gnb_dl_config_stats.proto](../codelets/fapi_dl_conf/fapi_gnb_dl_config_stats.proto).

## 8.2. FAPI UL Configuration

### 8.2.1. [fapi_gnb_ul_config_stats_collect](../codelets/fapi_ul_conf/fapi_gnb_ul_config_stats_collect.cpp)
Binds to hook [fapi_ul_tti_request](srsran_hooks.md#322-fapi_ul_tti_request).

Collects statistics related to the FAPI Uplink Config Request messages.

### 8.2.2. [fapi_gnb_ul_config_stats_report](../codelets/fapi_ul_conf/fapi_gnb_ul_config_stats_report.cpp)
Binds to hook [report_stats](srsran_hooks.md#121-report_stats).  

Sends messages as defined in [fapi_gnb_ul_config_stats.proto](../codelets/fapi_ul_conf/fapi_gnb_ul_config_stats.proto).

## 8.3. FAPI UL CRC

### 8.3.1. [fapi_gnb_crc_stats_collect](../codelets/fapi_ul_crc/fapi_gnb_crc_stats_collect.cpp)
Binds to hook [fapi_ul_tti_request](srsran_hooks.md#312-fapi_crc_indication).

Collects statistics related to the FAPI CRC indications.

### 8.3.2. [fapi_gnb_crc_stats_report](../codelets/fapi_ul_crc/fapi_gnb_crc_stats_report.cpp)
Binds to hook [report_stats](srsran_hooks.md#121-report_stats).  

Sends messages as defined in [fapi_gnb_crc_stats.proto](../codelets/fapi_ul_crc/fapi_gnb_crc_stats.proto).

## 8.4. FAPI UL RACH

### 8.4.1. [fapi_gnb_rach_stats_collect](../codelets/fapi_rach/fapi_gnb_rach_stats_collect.cpp)
Binds to hook [fapi_ul_tti_request](srsran_hooks.md#315-fapi_rach_indication).

Collects statistics related to the FAPI RACH messages.
 
### 8.4.2. [fapi_gnb_rach_stats_report](../codelets/fapi_rach/fapi_gnb_rach_stats_report.cpp)
Binds to hook [report_stats](srsran_hooks.md#121-report_stats).  

Sends messages as defined in [fapi_gnb_rach_stats.proto](../codelets/fapi_rach/fapi_gnb_rach_stats.proto).

# 9. XRAN Packets

These codelets are used to calulate inter-arrival statistics, and packet counts, for uplink and downlink directions.
For downlink, seperate statistics are collected for data and control packets.  For uplink, statistics are only colledcted for data.

## 9.1. [xran_packets_collect](../codelets/xran_packets/xran_packets_collect.c)
Binds to hook [capture_xran_packet](srsran_hooks.md#21-capture_xran_packet).

## 9.2. [xran_packets_report](../codelets/xran_packets/xran_packets_report.c)
Binds to hook [report_stats](srsran_hooks.md#121-report_stats).  

Sends messages as defined in [xran_packet_info.proto](../codelets/xran_packets/xran_packet_info.proto).

# 10. Slice management

## 10.1. [slice_management](../codelets/slice_mgmt/slice_mgmt.cpp)
Binds to hook [mac_sched_slice_mgmt](srsran_hooks.md#121-mac_sched_slice_mgmt-control-hook).

This codelet is used to update the allocation of slices.

It works in conjunction with the [slice_mgmt](../jrtc_apps/slice_mgmt/slice_mgmt_app.py) Jrtc application.

# 11. Performance statistics

This codelet is used to collect statistics of the performace of the codelets.

It can be used to identify cases where codelets are taking longer than expected. It provides a logarithmic histogram with 64 bins, and approximates the 50th, 90th, 95th, and 99th percentiles.

## 11.1. [jbpf_stats_report](../codelets/perf/jbpf_stats_report.c)
Binds to hook [report_stats](srsran_hooks.md#131-report_stats).  

Sends messages as defined in [jbpf_stats_report.proto](../codelets/perf/jbpf_stats_report.proto).
