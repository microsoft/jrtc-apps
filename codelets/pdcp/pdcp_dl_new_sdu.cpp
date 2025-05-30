// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "pdcp_helpers.h"
#include "pdcp_dl_pkts.h"
#include "pdcp_dl_north_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"


struct jbpf_load_map_def SEC("maps") dl_north_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_dl_north = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(dl_north_stats),
    .max_entries = 1,
};
  
DEFINE_PROTOHASH_64(dl_north_hash, MAX_NUM_UE_RB);


#ifdef PDCP_REPORT_DL_DELAY_QUEUE
struct jbpf_load_map_def SEC("maps") sdu_events = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_sdu_events),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") sdu_queues = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_sdu_queues),
    .max_entries = 1,
};


DEFINE_PROTOHASH_64(delay_hash, MAX_SDU_IN_FLIGHT);
DEFINE_PROTOHASH_64(queue_hash, MAX_SDU_QUEUES);
#endif


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
    
#ifdef PDCP_REPORT_DL_DELAY_QUEUE
    t_sdu_events *events = (t_sdu_events *)jbpf_map_lookup_elem(&sdu_events, &zero_index);
    if (!events)
        return JBPF_CODELET_FAILURE;

    t_sdu_queues *queues = (t_sdu_queues *)jbpf_map_lookup_elem(&sdu_queues, &zero_index);
    if (!queues)
        return JBPF_CODELET_FAILURE;
#endif

    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&dl_north_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    dl_north_stats *out = (dl_north_stats *)jbpf_map_lookup_elem(&stats_map_dl_north, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;



    // out->timestamp = jbpf_time_get_ns();
    // out->cu_ue_index = pdcp_ctx.cu_ue_index;
    // out->is_srb = pdcp_ctx.is_srb;
    // out->rb_id = pdcp_ctx.rb_id;
    // out->rlc_mode = pdcp_ctx.rlc_mode;
    // out->sdu_length = ctx->srs_meta_data1 >> 32;
    // out->count = ctx->srs_meta_data1 & 0xFFFFFFFF;


    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(pdcp_ctx.is_srb, pdcp_ctx.rb_id);

    // Store SDU arrival time so we can calculate delay and queue size at the PDCP level
    uint32_t sdu_length = (uint32_t) (ctx->srs_meta_data1 >> 32);
    uint32_t count = (uint32_t) (ctx->srs_meta_data1 & 0xFFFFFFFF);
    uint32_t window_size = (uint32_t) (ctx->srs_meta_data2 & 0xFFFFFFFF);

#ifdef DEBUG_PRINT
    // jbpf_printf_debug("PDCP DL NEW SDU: cu_ue_index=%d, sdu_length=%d, count=%d\n", 
    //     pdcp_ctx.cu_ue_index, sdu_length, count);
    jbpf_printf_debug("PDCP DL NEW SDU: cu_ue_index=%d, rb_id=%d, count=%d\n", 
        pdcp_ctx.cu_ue_index, rb_id, count);
#endif

    int new_val = 0;


    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, dl_north_hash, pdcp_ctx.cu_ue_index, rb_id, new_val);
    if (new_val) {
        out->stats[ind % MAX_NUM_UE_RB].cu_ue_index = pdcp_ctx.cu_ue_index;
        out->stats[ind % MAX_NUM_UE_RB].is_srb = pdcp_ctx.is_srb;
        out->stats[ind % MAX_NUM_UE_RB].rb_id = pdcp_ctx.rb_id;

        out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.count = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.total = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.max = 0;
    }

    *not_empty_stats = 1;

    out->stats[ind % MAX_NUM_UE_RB].window.count++;
    out->stats[ind % MAX_NUM_UE_RB].window.total += window_size;
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

// Still not fully debugged so allowing to be disabled
#ifdef PDCP_REPORT_DL_DELAY_QUEUE

    uint64_t now_ns = jbpf_time_get_ns();
    uint32_t key1 = 
        ((uint64_t)(rb_id & 0xFFFF) << 15) << 1 | 
        ((uint64_t)(pdcp_ctx.cu_ue_index & 0xFFFF));
    ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(events, map, delay_hash, key1, count, new_val);

    // in normal behavior, we should not have a new value, since the element would be cleated by deliv/discard handlers.
    // however in cases where a ue gets deleted and another one gets created the same cu_ue_index,
    // we will find an old element.
    // therefore reset the values irrespective of new_val
    
    events->map[ind % MAX_SDU_IN_FLIGHT].sdu_arrival_ns = now_ns;
    events->map[ind % MAX_SDU_IN_FLIGHT].pdcpTx_ns = 0;
    events->map[ind % MAX_SDU_IN_FLIGHT].rlcTxStarted_ns = 0;
    events->map[ind % MAX_SDU_IN_FLIGHT].rlcDelivered_ns = 0;
    events->map[ind % MAX_SDU_IN_FLIGHT].sdu_length = sdu_length;

#ifdef DEBUG_PRINT
    jbpf_printf_debug("   NEW DELAY: cu_ue_index=%d, arrival_ns=%ld, sdu_length=%d\n", 
        pdcp_ctx.cu_ue_index, events->map[ind % MAX_SDU_IN_FLIGHT].sdu_arrival_ns, sdu_length);
#endif

    ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(queues, map, queue_hash, pdcp_ctx.cu_ue_index, rb_id, new_val);

    if (new_val) {
        queues->map[ind % MAX_SDU_QUEUES].pkts = 0;
        queues->map[ind % MAX_SDU_QUEUES].bytes = 0;
    }
    queues->map[ind % MAX_SDU_QUEUES].pkts ++;
    queues->map[ind % MAX_SDU_QUEUES].bytes += sdu_length;
#ifdef DEBUG_PRINT
    jbpf_printf_debug("   NEW QUEUE: cu_ue_index=%d, pkts=%ld, bytes=%d\n", 
        pdcp_ctx.cu_ue_index,
        queues->map[ind % MAX_SDU_QUEUES].pkts,
        queues->map[ind % MAX_SDU_QUEUES].bytes);
#endif
#endif // PDCP_REPORT_DL_DELAY_QUEUE

    return JBPF_CODELET_SUCCESS;
}
