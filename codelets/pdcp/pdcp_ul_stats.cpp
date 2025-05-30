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

struct jbpf_load_map_def SEC("maps") ul_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

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

    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&ul_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    ul_stats *out = (ul_stats *)jbpf_map_lookup_elem(&stats_map_ul, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;

    // out->timestamp = jbpf_time_get_ns();
    // out->cu_ue_index = pdcp_ctx.cu_ue_index;
    // out->is_srb = pdcp_ctx.is_srb;
    // out->rb_id = pdcp_ctx.rb_id;
    // out->rlc_mode = pdcp_ctx.rlc_mode;
    // out->sdu_length = ctx->srs_meta_data1 >> 32;
    // out->window_size = ctx->srs_meta_data1 & 0xFFFFFFFF;

    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(pdcp_ctx.is_srb, pdcp_ctx.rb_id);

    uint32_t sdu_length = (uint32_t )(ctx->srs_meta_data1 >> 32);
    uint32_t window_size = (uint32_t) (ctx->srs_meta_data1 & 0xFFFFFFFF);

#ifdef DEBUG_PRINT
    jbpf_printf_debug("PDCP UL SDU: cu_ue_index=%d, rb_id=%d, sdu_length=%d\n", 
        pdcp_ctx.cu_ue_index, rb_id, sdu_length);
#endif

    int new_val = 0;

    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, ul_hash, pdcp_ctx.cu_ue_index, rb_id, new_val);
    if (new_val) {
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
    }

    out->stats[ind % MAX_NUM_UE_RB].window.count++;
    out->stats[ind % MAX_NUM_UE_RB].window.total += window_size;
    if (out->stats[ind % MAX_NUM_UE_RB].window.min > window_size) {
        out->stats[ind % MAX_NUM_UE_RB].window.min = window_size;
    }
    if (out->stats[ind % MAX_NUM_UE_RB].window.max < window_size) {
        out->stats[ind % MAX_NUM_UE_RB].window.max = window_size;
    }

    out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.count++;
    out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.total += window_size;
    if (out->stats[ind % MAX_NUM_UE_RB].window.min > window_size) {
        out->stats[ind % MAX_NUM_UE_RB].window.min = window_size;
    }
    if (out->stats[ind % MAX_NUM_UE_RB].window.max < window_size) {
        out->stats[ind % MAX_NUM_UE_RB].window.max = window_size;
    }

    out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.count++; 
    out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.total += sdu_length;
    if (out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.min > sdu_length) {
        out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.min = sdu_length;
    }
    if (out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.max < sdu_length) {
        out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.max = sdu_length;
    }

    *not_empty_stats = 1;


    return JBPF_CODELET_SUCCESS;
}
