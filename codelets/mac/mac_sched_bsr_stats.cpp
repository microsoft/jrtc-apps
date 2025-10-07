// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "srsran/scheduler/scheduler_feedback_handler.h"

#include "mac_helpers.h"
#include "mac_sched_bsr_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#include "jbpf_defs.h"
#include "jbpf_helper.h"


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
    
    int new_val = 0;

    // Increase BSR count
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(out, stats, bsr_hash, mac_ctx.ue_index, new_val);
    if (new_val) {
        out->stats[ind % MAX_NUM_UE].du_ue_index = mac_ctx.ue_index;
        out->stats[ind % MAX_NUM_UE].cnt = 0;
        out->stats[ind % MAX_NUM_UE].bytes = 0;
    }
    out->stats[ind % MAX_NUM_UE].cnt++;

    // Accumulate bytes from reported LCGs without range-for (verifier-friendly).
    // NOTE: size() and data() are constexpr/inlined for static_vector and compile to plain field reads.
    size_t n = mac_ctx.reported_lcgs.size();
    if (n > srsran::MAX_NOF_LCGS) {
        // Defensive: cap to capacity so the verifier has a hard upper bound.
        n = srsran::MAX_NOF_LCGS;
    }

    // Get a raw pointer to the underlying array.
    const srsran::ul_bsr_lcg_report* base = mac_ctx.reported_lcgs.data();

    // Loop with a constant upper bound that the verifier can unroll.
    #pragma clang loop unroll(full)
    for (size_t i = 0; i < srsran::MAX_NOF_LCGS; ++i) {
        if (i >= n) {
            break;
        }

        const srsran::ul_bsr_lcg_report* rep = &base[i];

        // Per-element bounds check against ctx->data_end to keep the verifier happy.
        if ((const uint8_t*)rep + sizeof(*rep) > (const uint8_t*)ctx->data_end) {
            return JBPF_CODELET_FAILURE;
        }

        out->stats[ind % MAX_NUM_UE].bytes += rep->nof_bytes;
    }

    *not_empty_stats = 1;

    return JBPF_CODELET_SUCCESS;
}
