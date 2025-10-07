// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "srsran/scheduler/scheduler_feedback_handler.h"

#include "mac_sched_phr_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#define MAX_NUM_UE_CELL (128)

struct jbpf_load_map_def SEC("maps") phr_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_phr = {
  .type = JBPF_MAP_TYPE_ARRAY,
  .key_size = sizeof(int),
  .value_size = sizeof(phr_stats),
  .max_entries = 1,
};

DEFINE_PROTOHASH_64(phr_hash, MAX_NUM_UE_CELL);



//#define DEBUG_PRINT

extern "C" SEC("jbpf_ran_mac_sched")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_mac_sched_ctx *ctx = (jbpf_mac_sched_ctx *)state;
    
    const srsran::cell_ph_report& ph_report = *reinterpret_cast<const srsran::cell_ph_report*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&ph_report) + sizeof(srsran::cell_ph_report) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&phr_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    phr_stats *out = (phr_stats *)jbpf_map_lookup_elem(&stats_map_phr, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;



    out->timestamp = jbpf_time_get_ns();


    int new_val = 0;
    //uint64_t key = ((uint64_t)ctx->cell_id << 31) << 1 | (uint64_t)ctx->du_ue_index;
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, phr_hash, ctx->cell_id, ctx->du_ue_index, new_val);
    if (new_val) {
        out->stats[ind % MAX_NUM_UE_CELL].du_ue_index = ctx->du_ue_index;
        out->stats[ind % MAX_NUM_UE_CELL].cell_id = ctx->cell_id;
        out->stats[ind % MAX_NUM_UE_CELL].ph_min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_CELL].ph_max = 0;
        out->stats[ind % MAX_NUM_UE_CELL].p_cmax_min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_CELL].p_cmax_max = 0;
    }
    uint32_t ph_start = ph_report.ph.start();
    uint32_t ph_stop = ph_report.ph.stop();
    
    if (out->stats[ind % MAX_NUM_UE_CELL].ph_min > ph_start) {
        out->stats[ind % MAX_NUM_UE_CELL].ph_min = ph_start;
    }
    if (out->stats[ind % MAX_NUM_UE_CELL].ph_max < ph_stop) {
        out->stats[ind % MAX_NUM_UE_CELL].ph_max = ph_stop;
        
    }
    if (ph_report.p_cmax.has_value()) {
        uint32_t cmax_start = ph_report.p_cmax.value().start();
        uint32_t cmax_stop = ph_report.p_cmax.value().stop();

        if (out->stats[ind % MAX_NUM_UE_CELL].p_cmax_min > cmax_start) {
            out->stats[ind % MAX_NUM_UE_CELL].p_cmax_min = cmax_start;
        }
        if (out->stats[ind % MAX_NUM_UE_CELL].p_cmax_max < cmax_stop) {
            out->stats[ind % MAX_NUM_UE_CELL].p_cmax_max = cmax_stop;
        }
    }
    *not_empty_stats = 1;


    return JBPF_CODELET_SUCCESS;
}
