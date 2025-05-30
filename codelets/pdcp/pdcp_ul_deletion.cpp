// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "pdcp_helpers.h"
#include "pdcp_ul_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"


#define MAX_NUM_UE_RB (256)


struct jbpf_load_map_def SEC("maps") stats_map_ul = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(ul_stats),
    .max_entries = 1,
};
  
DEFINE_PROTOHASH_64(ul_hash, MAX_NUM_UE_RB);






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

    ul_stats *out = (ul_stats *)jbpf_map_lookup_elem(&stats_map_ul, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;    

    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(pdcp_ctx.is_srb, pdcp_ctx.rb_id);    

#ifdef DEBUG_PRINT
    jbpf_printf_debug("pdcp_ul_deletion: cu_ue_index=%d, rb_id=%d\n", 
        ue_index, rb_id);
#endif


    // When a bearer context is setup, we need to reset the last acked
    // At the beginning, 0 is not acked so set to "-1".
    int new_val = 0;
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, ul_hash, pdcp_ctx.cu_ue_index, rb_id, new_val);
    out->stats[ind % MAX_NUM_UE_RB].cu_ue_index = pdcp_ctx.cu_ue_index;
    out->stats[ind % MAX_NUM_UE_RB].is_srb = pdcp_ctx.is_srb;
    out->stats[ind % MAX_NUM_UE_RB].rb_id = pdcp_ctx.rb_id;
    out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.count = 0;
    out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.total = 0;
    out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.min = UINT32_MAX;
    out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.max = 0;
    out->stats[ind % MAX_NUM_UE_RB].window.count = 0;
    out->stats[ind % MAX_NUM_UE_RB].window.total = 0;
    out->stats[ind % MAX_NUM_UE_RB].window.min = UINT32_MAX;
    out->stats[ind % MAX_NUM_UE_RB].window.max = 0;
    

    return JBPF_CODELET_SUCCESS;
}