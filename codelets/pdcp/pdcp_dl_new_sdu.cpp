// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "pdcp_helpers.h"
#include "pdcp_dl_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"


struct jbpf_load_map_def SEC("maps") dl_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_dl = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(dl_stats),
    .max_entries = 1,
};
  
DEFINE_PROTOHASH_64(dl_hash, MAX_NUM_UE_RB);




//#define DEBUG_PRINT

extern "C" SEC("jbpf_srsran_generic")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_ran_generic_ctx *ctx = (jbpf_ran_generic_ctx *)state;
    
    const jbpf_pdcp_ctx_info& pdcp_ctx = *reinterpret_cast<const jbpf_pdcp_ctx_info*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&pdcp_ctx) + sizeof(jbpf_pdcp_ctx_info) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }
    
    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&dl_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    dl_stats *out = (dl_stats *)jbpf_map_lookup_elem(&stats_map_dl, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;


    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(pdcp_ctx.is_srb, pdcp_ctx.rb_id);

    // get data passed in metadata
    // uint32_t count = (uint32_t) (ctx->srs_meta_data1 >> 32);
    uint32_t sdu_length = (uint32_t) (ctx->srs_meta_data1 & 0xFFFFFFFF);

#ifdef DEBUG_PRINT
    jbpf_printf_debug("PDCP DL NEW SDU: cu_ue_index=%d, rb_id=%d, count=%d\n", 
        pdcp_ctx.cu_ue_index, rb_id, count);
#endif

    int new_val = 0;

    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, dl_hash, pdcp_ctx.cu_ue_index, rb_id, new_val);
    if (new_val) {
        PDCP_DL_STATS_INIT(out->stats[ind % MAX_NUM_UE_RB], pdcp_ctx.cu_ue_index, pdcp_ctx.is_srb, 
                           pdcp_ctx.rb_id, pdcp_ctx.rlc_mode);
    }
    // Handle case where "deletion" has occurred and rlc_mode has been cleared
    if (out->stats[ind % MAX_NUM_UE_RB].rlc_mode == JBPF_RLC_MODE_MAX) {
        PDCP_DL_STATS_INIT(out->stats[ind % MAX_NUM_UE_RB], pdcp_ctx.cu_ue_index, pdcp_ctx.is_srb, 
                           pdcp_ctx.rb_id, pdcp_ctx.rlc_mode);
    }

    const jbpf_queue_info_t* queue_info = &pdcp_ctx.window_info;
    if (!queue_info->used) {
        PDCP_STATS_UPDATE(out->stats[ind % MAX_NUM_UE_RB].pdu_window_pkts, queue_info->num_pkts);
        PDCP_STATS_UPDATE(out->stats[ind % MAX_NUM_UE_RB].pdu_window_bytes, queue_info->num_bytes);
    }

    // update sdu_new_bytes
    PDCP_TRAFFIC_STATS_UPDATE(out->stats[ind % MAX_NUM_UE_RB].sdu_new_bytes, sdu_length);

    *not_empty_stats = 1;

    return JBPF_CODELET_SUCCESS;
}
