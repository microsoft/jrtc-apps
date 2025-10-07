// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "srsran/scheduler/scheduler_feedback_handler.h"

#include "mac_helpers.h"
#include "mac_sched_harq_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"



#include "jbpf_defs.h"
#include "jbpf_helper.h"
#include "jbpf_helper_utils.h"
#include "../utils/stats_utils.h"

struct jbpf_load_map_def SEC("maps") dl_harq_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_dl_harq = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(harq_stats),
    .max_entries = 1,
};
  

DEFINE_PROTOHASH_32(dl_harq_hash, MAX_NUM_UE);



//#define DEBUG_PRINT

extern "C" SEC("jbpf_ran_mac_sched")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_mac_sched_ctx *ctx = (jbpf_mac_sched_ctx *)state;

    const jbpf_mac_sched_harq_ctx_info_dl& harq_info = *reinterpret_cast<const jbpf_mac_sched_harq_ctx_info_dl*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&harq_info) + sizeof(jbpf_mac_sched_harq_ctx_info_dl) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&dl_harq_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    harq_stats *out = (harq_stats *)jbpf_map_lookup_elem(&stats_map_dl_harq, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;


    int new_val = 0;

    // Increase loss count
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(out, stats, dl_harq_hash, ctx->du_ue_index, new_val);
    if (new_val) {
        MAC_HARQ_STATS_INIT_DL(out->stats[ind % MAX_NUM_UE], ctx->cell_id, ctx->rnti, ctx->du_ue_index);
        out->stats[ind % MAX_NUM_UE].max_nof_harq_retxs = harq_info.h.max_nof_harq_retxs;
        out->stats[ind % MAX_NUM_UE].mcs_table = harq_info.h.mcs_table;
    }

    if (reinterpret_cast<const uint8_t*>(&harq_info) + sizeof(jbpf_mac_sched_harq_ctx_info_dl) <= reinterpret_cast<const uint8_t*>(ctx->data_end)) {    

        // cons_retx
        STATS_UPDATE(out->stats[ind % MAX_NUM_UE].cons_retx, harq_info.h.nof_retxs); 

        // mcs
        STATS_UPDATE(out->stats[ind % MAX_NUM_UE].mcs, harq_info.h.mcs); 

        // perHarqTypeStats
        t_harq_type_stats& hts = out->stats[ind % MAX_NUM_UE].perHarqTypeStats[harq_info.h.harq_type % JBPF_HARQ_EVENT_NUM];
        hts.count++;
        TRAFFIC_STATS_UPDATE(hts.tbs_bytes, harq_info.h.tbs_bytes);
        STATS_UPDATE(hts.cqi, harq_info.cqi);
    }

    *not_empty_stats = 1;

    return JBPF_CODELET_SUCCESS;
}
