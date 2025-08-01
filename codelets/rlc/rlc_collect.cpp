// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "rlc_dl_stats.pb.h"
#include "rlc_ul_stats.pb.h"



#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define MAX_NUM_UE_RB (256)



//// DL

jbpf_ringbuf_map(output_map_dl, rlc_dl_stats, 1000);

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_dl = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(rlc_dl_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(dl_hash, MAX_NUM_UE_RB);

struct jbpf_load_map_def SEC("maps") dl_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};




//// UL

jbpf_ringbuf_map(output_map_ul, rlc_ul_stats, 1000);

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_ul = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(rlc_ul_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(ul_hash, MAX_NUM_UE_RB);

struct jbpf_load_map_def SEC("maps") ul_not_empty = {
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
    ///// DL SOUTH stats

    uint32_t *not_empty_rlc_dl_stats = (uint32_t*)jbpf_map_lookup_elem(&dl_not_empty, &zero_index);
    if (!not_empty_rlc_dl_stats)
        return JBPF_CODELET_FAILURE;

    // Get stats map buffer to save output across invocations
    void* c = jbpf_map_lookup_elem(&stats_map_dl, &zero_index);
    if (!c)
        return JBPF_CODELET_FAILURE;
    rlc_dl_stats *out_dl = (rlc_dl_stats *)c;

        
    if (*not_empty_rlc_dl_stats)
    {
        out_dl->timestamp = timestamp;
        int ret = 0;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("DL OUTPUT: %lu\n", out_dl->timestamp);
#endif
        ret = jbpf_ringbuf_output(&output_map_dl, (void *) out_dl, sizeof(rlc_dl_stats));

        JBPF_HASHMAP_CLEAR(&dl_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_dl);

        *not_empty_rlc_dl_stats = 0;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }

    }




    ////////////////////////////////////////////////////////////////////////////////
    ///// UL stats

    uint32_t *not_empty_rlc_ul_stats = (uint32_t*)jbpf_map_lookup_elem(&ul_not_empty, &zero_index);
    if (!not_empty_rlc_ul_stats) {
        return JBPF_CODELET_FAILURE;
    }

    rlc_ul_stats *out_ul = (rlc_ul_stats *)jbpf_map_lookup_elem(&stats_map_ul, &zero_index);
    if (!out_ul)
        return JBPF_CODELET_FAILURE;

    if (*not_empty_rlc_ul_stats)
    {
        out_ul->timestamp = timestamp;

        int ret = 0;
#ifdef DEBUG_PRINT
        jbpf_printf_debug("UL OUTPUT: %lu\n", out_ul->timestamp);
#endif
        ret = jbpf_ringbuf_output(&output_map_ul, (void *) out_ul, sizeof(rlc_ul_stats));

        JBPF_HASHMAP_CLEAR(&ul_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_ul);

        *not_empty_rlc_ul_stats = 0;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }

    }


    return JBPF_CODELET_SUCCESS;
}
