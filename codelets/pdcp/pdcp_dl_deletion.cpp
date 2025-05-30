// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "pdcp_helpers.h"
#include "pdcp_dl_pkts.h"
#include "pdcp_dl_north_stats.pb.h"
#include "pdcp_dl_south_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"


#define MAX_NUM_UE_RB (256)

//// DL NORTH

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_dl_north = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(dl_north_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(dl_north_hash, MAX_NUM_UE_RB);

//// DL SOUTH

jbpf_ringbuf_map(output_map_dl_south, dl_south_stats, 1000);

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_dl_south = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(dl_south_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(dl_south_hash, MAX_NUM_UE_RB);


//// Notif trackers

struct jbpf_load_map_def SEC("maps") last_notif_acked_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_last_acked),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") last_deliv_acked_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_last_acked),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(last_notif_acked_hash, MAX_NUM_UE_RB);
DEFINE_PROTOHASH_64(last_deliv_acked_hash, MAX_NUM_UE_RB);

DEFINE_PROTOHASH_64(queue_hash, MAX_SDU_QUEUES);



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

    t_last_acked *last_notif_acked = (t_last_acked*)jbpf_map_lookup_elem(&last_notif_acked_map, &zero_index);
    if (!last_notif_acked) {
        return JBPF_CODELET_FAILURE;
    }

    t_last_acked *last_deliv_acked = (t_last_acked*)jbpf_map_lookup_elem(&last_deliv_acked_map, &zero_index);
    if (!last_deliv_acked) {
        return JBPF_CODELET_FAILURE;
    }

    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(pdcp_ctx.is_srb, pdcp_ctx.rb_id);    

#ifdef DEBUG_PRINT
    jbpf_printf_debug("pdcp_dl_deletion: cu_ue_index=%d, rb_id=%d\n", 
        ue_index, rb_id);
#endif


    // When a bearer context is setup, we need to reset the last acked
    // At the beginning, 0 is not acked so set to "-1".
    int new_val = 0;
    uint32_t ack_ind = 0;
    
    ack_ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(last_notif_acked, ack, last_notif_acked_hash, rb_id, pdcp_ctx.cu_ue_index, new_val);
    last_notif_acked->ack[ack_ind % MAX_NUM_UE_RB] = UINT32_MAX;

    ack_ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(last_deliv_acked, ack, last_deliv_acked_hash, rb_id, pdcp_ctx.cu_ue_index, new_val);
    last_deliv_acked->ack[ack_ind % MAX_NUM_UE_RB] = UINT32_MAX;

    dl_north_stats *dln_out = (dl_north_stats *)jbpf_map_lookup_elem(&stats_map_dl_north, &zero_index);
    if (!dln_out)
        return JBPF_CODELET_FAILURE;
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(dln_out, stats, dl_north_hash, pdcp_ctx.cu_ue_index, rb_id, new_val);
    dln_out->stats[ind % MAX_NUM_UE_RB].cu_ue_index = pdcp_ctx.cu_ue_index;
    dln_out->stats[ind % MAX_NUM_UE_RB].is_srb = pdcp_ctx.is_srb;
    dln_out->stats[ind % MAX_NUM_UE_RB].rb_id = pdcp_ctx.rb_id;
    dln_out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.count = 0;
    dln_out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.total = 0;
    dln_out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.min = UINT32_MAX;
    dln_out->stats[ind % MAX_NUM_UE_RB].sdu_bytes.max = 0;



    dl_south_stats *dls_out = (dl_south_stats *)jbpf_map_lookup_elem(&stats_map_dl_south, &zero_index);
    if (!dls_out)
        return JBPF_CODELET_FAILURE;
    ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(dls_out, stats, dl_south_hash, rb_id, pdcp_ctx.cu_ue_index, new_val);

    dls_out->stats[ind % MAX_NUM_UE_RB].cu_ue_index = pdcp_ctx.cu_ue_index;
    dls_out->stats[ind % MAX_NUM_UE_RB].is_srb = pdcp_ctx.is_srb;
    dls_out->stats[ind % MAX_NUM_UE_RB].rb_id = pdcp_ctx.rb_id;
    dls_out->stats[ind % MAX_NUM_UE_RB].window.count = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].window.total = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].window.min = UINT32_MAX;
    dls_out->stats[ind % MAX_NUM_UE_RB].window.max = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.count = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.total = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.min = UINT32_MAX;
    dls_out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.max = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].rlc_tx_delay.count = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].rlc_tx_delay.total = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].rlc_tx_delay.min = UINT32_MAX;
    dls_out->stats[ind % MAX_NUM_UE_RB].rlc_tx_delay.max = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].rlc_deliv_delay.count = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].rlc_deliv_delay.total = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].rlc_deliv_delay.min = UINT32_MAX;
    dls_out->stats[ind % MAX_NUM_UE_RB].rlc_deliv_delay.max = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].total_delay.count = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].total_delay.total = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].total_delay.min = UINT32_MAX;
    dls_out->stats[ind % MAX_NUM_UE_RB].total_delay.max = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].tx_queue_bytes.count = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].tx_queue_bytes.total = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].tx_queue_bytes.min = UINT32_MAX;
    dls_out->stats[ind % MAX_NUM_UE_RB].tx_queue_bytes.max = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].tx_queue_pkt.count = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].tx_queue_pkt.total = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].tx_queue_pkt.min = UINT32_MAX;
    dls_out->stats[ind % MAX_NUM_UE_RB].tx_queue_pkt.max = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].sdu_tx_bytes.count = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].sdu_tx_bytes.total = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].sdu_retx_bytes.count = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].sdu_retx_bytes.total = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].sdu_discarded_bytes.count = 0;
    dls_out->stats[ind % MAX_NUM_UE_RB].sdu_discarded_bytes.total = 0;

    // clear the queue hash entries
    uint64_t compound_key = ((uint64_t)rb_id << 31) << 1 | (uint64_t)pdcp_ctx.cu_ue_index; 
    jbpf_map_delete_elem(&queue_hash, &compound_key); 
    


    return JBPF_CODELET_SUCCESS;
}