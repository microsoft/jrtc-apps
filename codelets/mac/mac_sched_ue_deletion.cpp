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

#include "mac_helpers.h"

#include "mac_sched_bsr_stats.pb.h"
#include "mac_sched_crc_stats.pb.h"
#include "mac_sched_uci_stats.pb.h"
#include "mac_sched_harq_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"



#include "jbpf_defs.h"
#include "jbpf_helper.h"
#include "jbpf_helper_utils.h"




struct jbpf_load_map_def SEC("maps") stats_map_bsr = {
  .type = JBPF_MAP_TYPE_ARRAY,
  .key_size = sizeof(int),
  .value_size = sizeof(bsr_stats),
  .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_crc = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(crc_stats),
    .max_entries = 1,
};
  
struct jbpf_load_map_def SEC("maps") stats_map_uci = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uci_stats),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_dl_harq = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(harq_stats),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_ul_harq = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(harq_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_32(bsr_hash, MAX_NUM_UE);
DEFINE_PROTOHASH_32(crc_hash, MAX_NUM_UE);
DEFINE_PROTOHASH_32(uci_hash, MAX_NUM_UE);
DEFINE_PROTOHASH_32(dl_harq_hash, MAX_NUM_UE);
DEFINE_PROTOHASH_32(ul_harq_hash, MAX_NUM_UE);





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

    uci_stats *uci_out = (uci_stats *)jbpf_map_lookup_elem(&stats_map_uci, &zero_index);
    if (!uci_out)
        return JBPF_CODELET_FAILURE;

    harq_stats *dl_harq_out = (harq_stats *)jbpf_map_lookup_elem(&stats_map_dl_harq, &zero_index);
    if (!dl_harq_out)
        return JBPF_CODELET_FAILURE;

    harq_stats *ul_harq_out = (harq_stats *)jbpf_map_lookup_elem(&stats_map_ul_harq, &zero_index);
    if (!ul_harq_out)
        return JBPF_CODELET_FAILURE;


    int new_val = 0;

    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(bsr_out, stats, bsr_hash, ctx->du_ue_index, new_val);
    bsr_out->stats[ind % MAX_NUM_UE].cnt = 0;
    bsr_out->stats[ind % MAX_NUM_UE].bytes = 0;

    ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(crc_out, stats, crc_hash, ctx->du_ue_index, new_val);
    uint16_t MAX_NUM_RETX_HIST = (sizeof(crc_out->stats[ind % MAX_NUM_UE].retx_hist) / sizeof(crc_out->stats[ind % MAX_NUM_UE].retx_hist[0]));
    crc_out->stats[ind % MAX_NUM_UE].cons_max = 0;
    crc_out->stats[ind % MAX_NUM_UE].succ_tx = 0;
    crc_out->stats[ind % MAX_NUM_UE].cnt_tx = 0;
    for (int i = 0; i < MAX_NUM_RETX_HIST; ++i) {
        crc_out->stats[ind % MAX_NUM_UE].retx_hist[i] = 0;
    }
    crc_out->stats[ind % MAX_NUM_UE].harq_failure = 0;
    crc_out->stats[ind % MAX_NUM_UE].min_sinr = INT16_MAX;
    crc_out->stats[ind % MAX_NUM_UE].max_sinr = INT16_MIN;
    crc_out->stats[ind % MAX_NUM_UE].sum_sinr = 0;
    crc_out->stats[ind % MAX_NUM_UE].cnt_sinr = 0;
    crc_out->stats[ind % MAX_NUM_UE].min_rsrp = UINT32_MAX;
    crc_out->stats[ind % MAX_NUM_UE].max_rsrp = 0;
    crc_out->stats[ind % MAX_NUM_UE].sum_rsrp = 0;
    crc_out->stats[ind % MAX_NUM_UE].cnt_rsrp = 0;

    ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(uci_out, stats, uci_hash, ctx->du_ue_index, new_val);
    uci_out->stats[ind % MAX_NUM_UE].du_ue_index = ctx->du_ue_index;
    uci_out->stats[ind % MAX_NUM_UE].sr_detected = 0;
    uci_out->stats[ind % MAX_NUM_UE].time_advance_offset.count = 0;
    uci_out->stats[ind % MAX_NUM_UE].time_advance_offset.total = 0;
    uci_out->stats[ind % MAX_NUM_UE].time_advance_offset.min = UINT32_MAX;
    uci_out->stats[ind % MAX_NUM_UE].time_advance_offset.max = 0;
    uci_out->stats[ind % MAX_NUM_UE].has_time_advance_offset = false;
    uci_out->stats[ind % MAX_NUM_UE].csi.ri.count = 0;
    uci_out->stats[ind % MAX_NUM_UE].csi.ri.total = 0;
    uci_out->stats[ind % MAX_NUM_UE].csi.ri.min = UINT32_MAX;
    uci_out->stats[ind % MAX_NUM_UE].csi.ri.max = 0;
    uci_out->stats[ind % MAX_NUM_UE].csi.has_ri = false;
    uci_out->stats[ind % MAX_NUM_UE].csi.cqi.count = 0;
    uci_out->stats[ind % MAX_NUM_UE].csi.cqi.total = 0;
    uci_out->stats[ind % MAX_NUM_UE].csi.cqi.min = UINT32_MAX;
    uci_out->stats[ind % MAX_NUM_UE].csi.cqi.max = 0;
    uci_out->stats[ind % MAX_NUM_UE].csi.has_cqi = false;
    uci_out->stats[ind % MAX_NUM_UE].has_csi = false;

    ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(dl_harq_out, stats, dl_harq_hash, ctx->du_ue_index, new_val);
    MAC_HARQ_STATS_INIT_DL(dl_harq_out->stats[ind % MAX_NUM_UE], ctx->cell_id, ctx->rnti, ctx->du_ue_index);

    ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(ul_harq_out, stats, ul_harq_hash, ctx->du_ue_index, new_val);
    MAC_HARQ_STATS_INIT_UL(ul_harq_out->stats[ind % MAX_NUM_UE], ctx->cell_id, ctx->rnti, ctx->du_ue_index);

    return JBPF_CODELET_SUCCESS;
}
