// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

//
// Stats are collected for a 1-sec peiod, per ue_index.
// Wehn UE are deleted/created, the ue_index can be re-used.  This mans that for a given stats period, an index could 
// be used by multiple UEs.  
// To not give false positives, we clear he stats when a UE is deleted.
//


#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "srsran/scheduler/scheduler_feedback_handler.h"

#include "mac_sched_bsr_stats.pb.h"
#include "mac_sched_crc_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"



#include "jbpf_defs.h"
#include "jbpf_helper.h"
#include "jbpf_helper_utils.h"

#define MAX_NUM_UE (32)


struct jbpf_load_map_def SEC("maps") stats_map_bsr = {
  .type = JBPF_MAP_TYPE_ARRAY,
  .key_size = sizeof(int),
  .value_size = sizeof(bsr_stats),
  .max_entries = 1,
};

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_crc = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(crc_stats),
    .max_entries = 1,
};
  

DEFINE_PROTOHASH_32(bsr_hash, MAX_NUM_UE);
DEFINE_PROTOHASH_32(crc_hash, MAX_NUM_UE);





//#define DEBUG_PRINT

extern "C" SEC("jbpf_ran_mac_sched")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_mac_sched_ctx *ctx = (jbpf_mac_sched_ctx *)state;
    


    bsr_stats *bsr_out = (bsr_stats *)jbpf_map_lookup_elem(&stats_map_bsr, &zero_index);
    if (!bsr_out)
        return JBPF_CODELET_FAILURE;

    crc_stats *crc_out = (crc_stats *)jbpf_map_lookup_elem(&stats_map_crc, &zero_index);
    if (!crc_out)
        return JBPF_CODELET_FAILURE;



    int new_val = 0;

    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(bsr_out, stats, bsr_hash, ctx->du_ue_index, new_val);
    bsr_out->stats[ind % MAX_NUM_UE].cnt = 0;

    ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(crc_out, stats, crc_hash, ctx->du_ue_index, new_val);
    crc_out->stats[ind % MAX_NUM_UE].cons_min = UINT32_MAX;
    crc_out->stats[ind % MAX_NUM_UE].cons_max = 0;
    crc_out->stats[ind % MAX_NUM_UE].succ_tx = 0;
    crc_out->stats[ind % MAX_NUM_UE].cnt_tx = 0;
    crc_out->stats[ind % MAX_NUM_UE].min_sinr = UINT32_MAX;
    crc_out->stats[ind % MAX_NUM_UE].min_rsrp = UINT32_MAX;
    crc_out->stats[ind % MAX_NUM_UE].max_sinr = 0;
    crc_out->stats[ind % MAX_NUM_UE].max_rsrp = INT32_MIN;
    crc_out->stats[ind % MAX_NUM_UE].sum_sinr = 0;
    crc_out->stats[ind % MAX_NUM_UE].sum_rsrp = 0;
    crc_out->stats[ind % MAX_NUM_UE].cnt_sinr = 0;
    crc_out->stats[ind % MAX_NUM_UE].cnt_rsrp = 0;

    
    return JBPF_CODELET_SUCCESS;
}
