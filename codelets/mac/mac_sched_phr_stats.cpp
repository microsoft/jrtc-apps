// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "srsran/scheduler/scheduler_feedback_handler.h"
#include "srsran/mac/phr_report.h"

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
    
    const srsran::ul_phr_indication_message& mac_ctx = *reinterpret_cast<const srsran::ul_phr_indication_message*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&mac_ctx) + sizeof(srsran::ul_phr_indication_message) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
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
    //out->ue_index = ctx->du_ue_index;
    //out->rnti = (uint32_t) mac_ctx.rnti;



    // NOTE: here I cannot use this call:
    // struct srsran::cell_ph_report rep = static_cast<srsran::cell_ph_report>(mac_ctx.phr.get_se_phr());
    // This seems to be because get_se_phr() calls standard method back() which doesn't seem to verify. 

    auto ph_reports = mac_ctx.phr.get_phr();
    for (int i=0; i<srsran::MAX_NOF_DU_CELLS; i++) {
        if (i < ph_reports.size()) {
            int new_val = 0;
            //uint64_t key = ((uint64_t)ph_reports[i].serv_cell_id << 31) << 1 | (uint64_t)ctx->du_ue_index;
            uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, phr_hash, ph_reports[i].serv_cell_id, ctx->du_ue_index, new_val);
            if (new_val) {
                out->stats[ind % MAX_NUM_UE_CELL].ph_min = UINT32_MAX;
                out->stats[ind % MAX_NUM_UE_CELL].ph_max = 0;
                out->stats[ind % MAX_NUM_UE_CELL].p_cmax_min = UINT32_MAX;
                out->stats[ind % MAX_NUM_UE_CELL].p_cmax_max = 0;
            }
            if (out->stats[ind % MAX_NUM_UE_CELL].ph_min > ph_reports[i].ph.start()) {
                out->stats[ind % MAX_NUM_UE_CELL].ph_min = ph_reports[i].ph.start();
            }
            if (out->stats[ind % MAX_NUM_UE_CELL].ph_max < ph_reports[i].ph.stop()) {
                out->stats[ind % MAX_NUM_UE_CELL].ph_max = ph_reports[i].ph.stop();
                
            }
            // out->ph_reports[i].ph_min = ph_reports[i].ph.start();
            // out->ph_reports[i].ph_max = ph_reports[i].ph.stop();
            if (ph_reports[i].p_cmax.has_value()) {
                if (out->stats[ind % MAX_NUM_UE_CELL].p_cmax_min > ph_reports[i].p_cmax.value().start()) {
                    out->stats[ind % MAX_NUM_UE_CELL].p_cmax_min = ph_reports[i].p_cmax.value().start();
                }
                if (out->stats[ind % MAX_NUM_UE_CELL].p_cmax_max < ph_reports[i].p_cmax.value().stop()) {
                    out->stats[ind % MAX_NUM_UE_CELL].p_cmax_max = ph_reports[i].p_cmax.value().stop();
                }
                // out->ph_reports[i].p_cmax_min = ph_reports[i].p_cmax.value().start();
                // out->ph_reports[i].p_cmax_max = ph_reports[i].p_cmax.value().stop();
            }
            *not_empty_stats = 1;
        } else {
            break;
        }
    }


    return JBPF_CODELET_SUCCESS;
}
