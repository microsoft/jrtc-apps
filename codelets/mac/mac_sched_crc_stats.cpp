// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "srsran/scheduler/scheduler_feedback_handler.h"

#include "mac_helpers.h"
#include "mac_sched_crc_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"



#include "jbpf_defs.h"
#include "jbpf_helper.h"
#include "jbpf_helper_utils.h"



struct jbpf_load_map_def SEC("maps") crc_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_crc = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(crc_stats),
    .max_entries = 1,
};
  

DEFINE_PROTOHASH_32(crc_hash, MAX_NUM_UE);



//#define MAX_NUM_RETX_HIST 16


//#define DEBUG_PRINT

extern "C" SEC("jbpf_ran_mac_sched")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_mac_sched_ctx *ctx = (jbpf_mac_sched_ctx *)state;
    
    const srsran::ul_crc_pdu_indication& mac_ctx = *reinterpret_cast<const srsran::ul_crc_pdu_indication*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&mac_ctx) + sizeof(srsran::ul_crc_pdu_indication) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&crc_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    crc_stats *out = (crc_stats *)jbpf_map_lookup_elem(&stats_map_crc, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;

    bool processed = (bool) (ctx->srs_meta_data1 >> 32);        
    uint16_t nof_retxs = (uint16_t) (ctx->srs_meta_data1 >> 16) & 0xffff;
    uint16_t max_nof_retxs = (uint16_t) (ctx->srs_meta_data1 & 0xffff);

    if (!processed) {
        return JBPF_CODELET_SUCCESS;
    }

    int new_val = 0;

    // Increase loss count
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(out, stats, crc_hash, ctx->du_ue_index, new_val);

    uint16_t MAX_NUM_RETX_HIST = (sizeof(out->stats[ind % MAX_NUM_UE].retx_hist) / sizeof(out->stats[ind % MAX_NUM_UE].retx_hist[0]));

    if (new_val) {
        out->stats[ind % MAX_NUM_UE].cons_max = 0;
        out->stats[ind % MAX_NUM_UE].succ_tx = 0;
        out->stats[ind % MAX_NUM_UE].cnt_tx = 0;
        for (int i = 0; i < MAX_NUM_RETX_HIST; ++i) {
            out->stats[ind % MAX_NUM_UE].retx_hist[i] = 0;
        }
        out->stats[ind % MAX_NUM_UE].harq_failure = 0;

        // Initialise to int16 limits as original SINR is an int16
        out->stats[ind % MAX_NUM_UE].min_sinr = INT16_MAX;
        out->stats[ind % MAX_NUM_UE].max_sinr = INT16_MIN;
        out->stats[ind % MAX_NUM_UE].sum_sinr = 0;
        out->stats[ind % MAX_NUM_UE].cnt_sinr = 0;

        out->stats[ind % MAX_NUM_UE].min_rsrp = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE].max_rsrp = 0;
        out->stats[ind % MAX_NUM_UE].sum_rsrp = 0;
        out->stats[ind % MAX_NUM_UE].cnt_rsrp = 0;
    }



    //////////////// Loss stats

    out->stats[ind % MAX_NUM_UE].cnt_tx++;

    auto retx_hist_idx = (nof_retxs > MAX_NUM_RETX_HIST) ? (MAX_NUM_RETX_HIST) : nof_retxs;
    out->stats[ind % MAX_NUM_UE].retx_hist[retx_hist_idx % MAX_NUM_RETX_HIST]++;

    if (mac_ctx.tb_crc_success)
    {
        out->stats[ind % MAX_NUM_UE].succ_tx++;

    } else {

        // Increase max "consecutive loss" count
        if (out->stats[ind].cons_max < (uint32_t)(nof_retxs)) {
            out->stats[ind].cons_max = (uint32_t)(nof_retxs);
#ifdef DEBUG_PRINT
        jbpf_printf_debug("Min/max: ue=%d max=%d\n",
            ctx->du_ue_index, 
            out->stats[ind].cons_max);
#endif
        }

        // if not ack and h.nof_retxs >= h.max_nof_harq_retxs
        if (nof_retxs >= max_nof_retxs) {
            // Handle max HARQ retransmissions reached
             out->stats[ind].harq_failure++;
        }
    }





    //////////////// RSRP/RSRQ stats


    if (mac_ctx.ul_sinr_dB.has_value()) {

        // valid range of ul_sinr_dB is [-65.534, 65.534]

        // We ignore decimal part of SINR
        int32_t ul_sinr_dB = (int32_t)fixedpt_toint(float_to_fixed(mac_ctx.ul_sinr_dB.value()));
        if (ul_sinr_dB < out->stats[ind].min_sinr) {
            out->stats[ind].min_sinr = ul_sinr_dB;
        }
        if (ul_sinr_dB > out->stats[ind].max_sinr) {
            out->stats[ind].max_sinr = ul_sinr_dB;
        }
        out->stats[ind].sum_sinr += ul_sinr_dB;
        out->stats[ind].cnt_sinr++;
#ifdef DEBUG_PRINT
        jbpf_printf_debug("SINR: ue=%d SINR=%d sum_sinr=%d\n",
            ctx->du_ue_index, 
            ul_sinr_dB,
            out->stats[ind].sum_sinr
        );
        jbpf_printf_debug("      min_sinr=%d max_sinr=%d cnt=%d\n",
            out->stats[ind].min_sinr, 
            out->stats[ind].max_sinr, 
            out->stats[ind].cnt_sinr
        );
#endif
    } 

    if (mac_ctx.ul_rsrp_dBFS.has_value()) {

        // valid range of ul_rsrp_dBFS is [-128.0, 6425.4]

        // We ignore decimal part of RSRP
        int32_t ul_rsrp_dB = (int32_t) fixedpt_toint(float_to_fixed(mac_ctx.ul_rsrp_dBFS.value()));

        if (ul_rsrp_dB < out->stats[ind].min_rsrp) {
            out->stats[ind].min_rsrp = ul_rsrp_dB;
        }
        if (ul_rsrp_dB > out->stats[ind].max_rsrp) {
            out->stats[ind].max_rsrp = ul_rsrp_dB;
        }
        out->stats[ind].sum_rsrp += ul_rsrp_dB;
        out->stats[ind].cnt_rsrp++;
#ifdef DEBUG_PRINT
        jbpf_printf_debug("RSRP: ue=%d RSRP=%d sum_rsrp=%d\n",
            ctx->du_ue_index, 
            ul_rsrp_dB,
            out->stats[ind].sum_rsrp
        );
        jbpf_printf_debug("      min_rsrp=%d max_rsrp=%d cnt=%d\n",
            out->stats[ind].min_rsrp, 
            out->stats[ind].max_rsrp, 
            out->stats[ind].cnt_rsrp
        );
#endif
    }

    *not_empty_stats = 1;

    // if (mac_ctx.time_advance_offset.has_value()) {
    //     // Check phy_time_unit.to_seconds() to see how to convert to seconds
    //     out->time_advance_offset = (int32_t) (mac_ctx.time_advance_offset.value().to_Tc());
    // } else {
    //     out->time_advance_offset = 0;
    // }
    //out->ul_sinr_dB = mac_ctx.ul_sinr_dB.has_value() ? static_cast<uint32_t>(mac_ctx.ul_sinr_dB.value() * 1000.0 + 0.5) : 0;
    //out->ul_rsrp_dBFS = mac_ctx.ul_rsrp_dBFS.has_value() ? static_cast<uint32_t>(mac_ctx.ul_rsrp_dBFS.value() * 1000.0 + 0.5) : 0;
    //out->time_advance_offset = mac_ctx.time_advance_offset.has_value() ? static_cast<uint32_t>(mac_ctx.time_advance_offset.value().to_seconds() * 1000000.0 + 0.5) : 0;

    
    return JBPF_CODELET_SUCCESS;
}
