// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "mac_sched_crc_stats.pb.h"
#include "mac_sched_bsr_stats.pb.h"
#include "mac_sched_phr_stats.pb.h"
#include "mac_sched_uci_stats.pb.h"
#include "mac_sched_harq_stats.pb.h"


#include "jbpf_defs.h"
#include "jbpf_helper.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"
#include "mac_helpers.h"


#define MAX_NUM_UE_CELL (128)


//// DL HARQ

jbpf_ringbuf_map(output_map_dl_harq, harq_stats, 1000);

struct jbpf_load_map_def SEC("maps") last_time_dl_harq = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint64_t),
    .max_entries = 1,
};

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_dl_harq = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(harq_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_32(dl_harq_hash, MAX_NUM_UE);

struct jbpf_load_map_def SEC("maps") dl_harq_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};



//// UL HARQ

jbpf_ringbuf_map(output_map_ul_harq, harq_stats, 1000);

struct jbpf_load_map_def SEC("maps") last_time_ul_harq = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint64_t),
    .max_entries = 1,
};

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_ul_harq = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(harq_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_32(ul_harq_hash, MAX_NUM_UE);

struct jbpf_load_map_def SEC("maps") ul_harq_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};





//#define DEBUG_PRINT 1

extern "C" SEC("jbpf_ran_layer2")
uint64_t jbpf_main(void *state)
{
    uint64_t zero_index = 0;
    uint64_t timestamp;

    // Timestamp field name should not change as it is hardcoded in post processing
    timestamp = jbpf_time_get_ns();

    // Timestamp is in ns, and we want to report pprox every second, so divide by 2^30 
    uint64_t timestamp32 = (uint64_t) (timestamp >> 30);
    

    ////////////////////////////////////////////////////////////////////////////////
    ///// DL HARQ stats

    uint32_t *not_empty_dl_harq_stats = (uint32_t*)jbpf_map_lookup_elem(&dl_harq_not_empty, &zero_index);
    if (!not_empty_dl_harq_stats)
        return JBPF_CODELET_FAILURE;

    // Get stats map buffer to save output across invocations
    void* c = jbpf_map_lookup_elem(&stats_map_dl_harq, &zero_index);
    if (!c)
        return JBPF_CODELET_FAILURE;
    harq_stats *out_dl_harq = (harq_stats *)c;

    uint64_t *last_timestamp_dl_harq = (uint64_t*)jbpf_map_lookup_elem(&last_time_dl_harq, &zero_index);
    if (!last_timestamp_dl_harq)
        return JBPF_CODELET_FAILURE;


    if (*not_empty_dl_harq_stats && *last_timestamp_dl_harq < timestamp32)
    {
        out_dl_harq->timestamp = timestamp;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("DL HARQ OUTPUT: %lu\n", out_dl_harq->timestamp);
#endif

        int ret = jbpf_ringbuf_output(&output_map_dl_harq, (void *) out_dl_harq, sizeof(harq_stats));

        JBPF_HASHMAP_CLEAR(&dl_harq_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_dl_harq);

        *not_empty_dl_harq_stats = 0;
        *last_timestamp_dl_harq = timestamp32;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }
    }    


    ////////////////////////////////////////////////////////////////////////////////
    ///// UL HARQ stats

    uint32_t *not_empty_ul_harq_stats = (uint32_t*)jbpf_map_lookup_elem(&ul_harq_not_empty, &zero_index);
    if (!not_empty_ul_harq_stats)
        return JBPF_CODELET_FAILURE;

    // Get stats map buffer to save output across invocations
    c = jbpf_map_lookup_elem(&stats_map_ul_harq, &zero_index);
    if (!c)
        return JBPF_CODELET_FAILURE;
    harq_stats *out_ul_harq = (harq_stats *)c;

    uint64_t *last_timestamp_ul_harq = (uint64_t*)jbpf_map_lookup_elem(&last_time_ul_harq, &zero_index);
    if (!last_timestamp_ul_harq)
        return JBPF_CODELET_FAILURE;


    if (*not_empty_ul_harq_stats && *last_timestamp_ul_harq < timestamp32)
    {
        out_ul_harq->timestamp = timestamp;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("DL HARQ OUTPUT: %lu\n", out_ul_harq->timestamp);
#endif

        int ret = jbpf_ringbuf_output(&output_map_ul_harq, (void *) out_ul_harq, sizeof(harq_stats));

        JBPF_HASHMAP_CLEAR(&ul_harq_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_ul_harq);

        *not_empty_ul_harq_stats = 0;
        *last_timestamp_ul_harq = timestamp32;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }
    }    



    return JBPF_CODELET_SUCCESS;
}
