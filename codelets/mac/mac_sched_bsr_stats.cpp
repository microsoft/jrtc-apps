// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "srsran/scheduler/scheduler_feedback_handler.h"

#include "mac_sched_bsr_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#include "jbpf_defs.h"
#include "jbpf_helper.h"

#define MAX_NUM_UE (32)


struct jbpf_load_map_def SEC("maps") bsr_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_bsr = {
  .type = JBPF_MAP_TYPE_ARRAY,
  .key_size = sizeof(int),
  .value_size = sizeof(bsr_stats),
  .max_entries = 1,
};

DEFINE_PROTOHASH_32(bsr_hash, MAX_NUM_UE);


//#define DEBUG_PRINT

extern "C" SEC("jbpf_ran_mac_sched")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_mac_sched_ctx *ctx = (jbpf_mac_sched_ctx *)state;
    
    const srsran::ul_bsr_indication_message& mac_ctx = *reinterpret_cast<const srsran::ul_bsr_indication_message*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&mac_ctx) + sizeof(srsran::ul_bsr_indication_message) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&bsr_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    bsr_stats *out = (bsr_stats *)jbpf_map_lookup_elem(&stats_map_bsr, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;
    

    // out->timestamp = jbpf_time_get_ns();
    // out->cell_index = mac_ctx.cell_index;
    // out->ue_index = ctx->du_ue_index;
    // out->crnti = (uint32_t) mac_ctx.crnti;
    // out->type = (uint32_t) mac_ctx.type;


    int new_val = 0;

    // Increase BSR count
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(out, stats, bsr_hash, ctx->du_ue_index, new_val);
    if (new_val) {
        out->stats[ind % MAX_NUM_UE].cnt = 0;
    }
    out->stats[ind % MAX_NUM_UE].cnt++;

    *not_empty_stats = 1;

    return JBPF_CODELET_SUCCESS;
}
