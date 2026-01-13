// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef JRTC_RLC_HELPERS_H
#define JRTC_RLC_HELPERS_H

#include "../utils/stats_utils.h"


#define MAX_NUM_UE_RB (256)


#define RLC_DL_STATS_INIT(dest, __du_ue_index, __is_srb, __rb_id, __rlc_mode)  \
    do {                                                                       \
        dest.du_ue_index = __du_ue_index;                                      \
        dest.is_srb = __is_srb;                                                \
        dest.rb_id = __rb_id;                                                  \
        dest.rlc_mode = __rlc_mode;                                            \
        STATS_INIT(dest.sdu_queue_pkts);                                   \
        STATS_INIT(dest.sdu_queue_bytes);                                  \
        TRAFFIC_STATS_INIT(dest.sdu_new_bytes);                            \
        TRAFFIC_STATS_INIT(dest.pdu_tx_bytes);                             \
        STATS_INIT(dest.sdu_tx_started);                                   \
        STATS_INIT(dest.sdu_tx_completed);                                 \
        STATS_INIT(dest.sdu_tx_delivered);                                 \
        dest.has_am = (rlc_ctx.rlc_mode == JBPF_RLC_MODE_AM);                  \
        if (dest.has_am) {                                                     \
            TRAFFIC_STATS_INIT(dest.am.pdu_retx_bytes);                    \
            TRAFFIC_STATS_INIT(dest.am.pdu_status_bytes);                  \
            STATS_INIT(dest.am.pdu_retx_count);                            \
            STATS_INIT(dest.am.pdu_window_pkts);                           \
            STATS_INIT(dest.am.pdu_window_bytes);                          \
        }                                                                      \
    } while (0)


#define RLC_UL_STATS_INIT(dest, __du_ue_index, __is_srb, __rb_id, __rlc_mode)  \
    do {                                                                       \
        dest.du_ue_index = __du_ue_index;                                      \
        dest.is_srb = __is_srb;                                                \
        dest.rb_id = __rb_id;                                                  \
        dest.rlc_mode = __rlc_mode;                                            \
        TRAFFIC_STATS_INIT(dest.pdu_bytes);                                \
        TRAFFIC_STATS_INIT(dest.sdu_delivered_bytes);                      \
        STATS_INIT(dest.sdu_delivered_latency);                            \
        dest.has_um = (rlc_ctx.rlc_mode == JBPF_RLC_MODE_UM);                  \
        if (dest.has_um) {                                                     \
            STATS_INIT(dest.um.pdu_window_pkts);                           \
        }                                                                      \
        dest.has_am = (rlc_ctx.rlc_mode == JBPF_RLC_MODE_AM);                  \
        if (dest.has_um) {                                                     \
            STATS_INIT(dest.am.pdu_window_pkts);                           \
        }                                                                      \
    } while (0)



#endif // JRTC_RLC_HELPERS_H