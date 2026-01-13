// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef JRTC_PDCP_HELPERS_H
#define JRTC_PDCP_HELPERS_H

#include "../utils/stats_utils.h"

#define MAX_NUM_UE_RB (256)

// PDCP passes :  0=UM, 1=AM
// JbpfRlcMode_t is: JBPF_RLC_MODE_TM=1, JBPF_RLC_MODE_UM=2, JBPF_RLC_MODE_AM=3
#define PDCP_RLCMODE_2_JBPF_RLCMODE(pdcp_rlc_mode) (pdcp_rlc_mode + 2)



#define PDCP_DL_STATS_INIT(dest, __cu_ue_index, __is_srb, __rb_id, __rlc_mode)  \
    do {                                                                        \
        dest.cu_ue_index = __cu_ue_index;                                       \
        dest.is_srb = __is_srb;                                                 \
        dest.rb_id = __rb_id;                                                   \
        dest.rlc_mode = PDCP_RLCMODE_2_JBPF_RLCMODE(__rlc_mode);                \
        TRAFFIC_STATS_INIT(dest.sdu_new_bytes);                            \
        dest.sdu_discarded = 0;                                                 \
        TRAFFIC_STATS_INIT(dest.data_pdu_tx_bytes);                        \
        TRAFFIC_STATS_INIT(dest.data_pdu_retx_bytes);                      \
        TRAFFIC_STATS_INIT(dest.control_pdu_tx_bytes);                     \
        STATS_INIT(dest.pdu_window_pkts);                                  \
        STATS_INIT(dest.pdu_window_bytes);                                 \
        STATS_INIT(dest.sdu_tx_latency);                                   \
    } while (0) 



#define PDCP_UL_STATS_INIT(dest, __cu_ue_index, __is_srb, __rb_id, __rlc_mode)  \
    do {                                                                \
        dest.cu_ue_index = __cu_ue_index;                               \
        dest.is_srb = __is_srb;                                         \
        dest.rb_id = __rb_id;                                           \
        dest.rlc_mode = PDCP_RLCMODE_2_JBPF_RLCMODE(__rlc_mode);        \
        TRAFFIC_STATS_INIT(dest.sdu_delivered_bytes);              \
        TRAFFIC_STATS_INIT(dest.rx_data_pdu_bytes);                \
        TRAFFIC_STATS_INIT(dest.rx_control_pdu_bytes);             \
        STATS_INIT(dest.pdu_window_pkts);                          \
        STATS_INIT(dest.pdu_window_bytes);                         \
    } while (0)



#endif // JRTC_PDCP_HELPERS_H
