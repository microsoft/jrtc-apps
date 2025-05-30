// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "pdcp_dl_north_stats.pb.h"
#include "pdcp_dl_south_stats.pb.h"
#include "pdcp_ul_stats.pb.h"

#include "pdcp_dl_pkts.h"

#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define MAX_NUM_UE_RB (256)



//// DL NORTH

jbpf_ringbuf_map(output_map_dl_north, dl_north_stats, 1000);


// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_dl_north = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(dl_north_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(dl_north_hash, MAX_NUM_UE_RB);

struct jbpf_load_map_def SEC("maps") dl_north_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};


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

struct jbpf_load_map_def SEC("maps") dl_south_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};




//// UL

jbpf_ringbuf_map(output_map_ul, ul_stats, 1000);

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_ul = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(ul_stats),
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
    ///// DL NORTH stats

    uint32_t *not_empty_dl_north_stats = (uint32_t*)jbpf_map_lookup_elem(&dl_north_not_empty, &zero_index);
    if (!not_empty_dl_north_stats)
        return JBPF_CODELET_FAILURE;

    // Get stats map buffer to save output across invocations
    void *c = jbpf_map_lookup_elem(&stats_map_dl_north, &zero_index);
    if (!c)
        return JBPF_CODELET_FAILURE;
    dl_north_stats *out_dl_north = (dl_north_stats *)c;

    if (*not_empty_dl_north_stats)
    {
        out_dl_north->timestamp = timestamp;

        int ret = 0;
#ifdef PDCP_REPORT_DL
#ifdef DEBUG_PRINT
        jbpf_printf_debug("DL NORTH OUTPUT: %lu\n", out_dl_north->timestamp);
#endif
        ret = jbpf_ringbuf_output(&output_map_dl_north, (void *) out_dl_north, sizeof(dl_north_stats));
#endif

        JBPF_HASHMAP_CLEAR(&dl_north_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_dl_north);

        *not_empty_dl_north_stats = 0;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }

    }



    ////////////////////////////////////////////////////////////////////////////////
    ///// DL SOUTH stats

    uint32_t *not_empty_dl_south_stats = (uint32_t*)jbpf_map_lookup_elem(&dl_south_not_empty, &zero_index);
    if (!not_empty_dl_south_stats)
        return JBPF_CODELET_FAILURE;

    // Get stats map buffer to save output across invocations
    c = jbpf_map_lookup_elem(&stats_map_dl_south, &zero_index);
    if (!c)
        return JBPF_CODELET_FAILURE;
    dl_south_stats *out_dl_south = (dl_south_stats *)c;

        
    if (*not_empty_dl_south_stats)
    {
        out_dl_south->timestamp = timestamp;
        int ret = 0;

#ifdef PDCP_REPORT_DL
#ifdef DEBUG_PRINT
        jbpf_printf_debug("DL SOUTH OUTPUT: %lu\n", out_dl_south->timestamp);
#endif
        ret = jbpf_ringbuf_output(&output_map_dl_south, (void *) out_dl_south, sizeof(dl_south_stats));
#endif

        JBPF_HASHMAP_CLEAR(&dl_south_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_dl_south);

        *not_empty_dl_south_stats = 0;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }

    }




    ////////////////////////////////////////////////////////////////////////////////
    ///// UL stats

    uint32_t *not_empty_ul_stats = (uint32_t*)jbpf_map_lookup_elem(&ul_not_empty, &zero_index);
    if (!not_empty_ul_stats) {
        return JBPF_CODELET_FAILURE;
    }

    ul_stats *out_ul = (ul_stats *)jbpf_map_lookup_elem(&stats_map_ul, &zero_index);
    if (!out_ul)
        return JBPF_CODELET_FAILURE;

    if (*not_empty_ul_stats)
    {
        out_ul->timestamp = timestamp;

        int ret = 0;
#ifdef PDCP_REPORT_UL
#ifdef DEBUG_PRINT
        jbpf_printf_debug("UL OUTPUT: %lu\n", out_ul->timestamp);
#endif
        ret = jbpf_ringbuf_output(&output_map_ul, (void *) out_ul, sizeof(ul_stats));
#endif // PDCP_REPORT_UL

        JBPF_HASHMAP_CLEAR(&ul_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_ul);

        *not_empty_ul_stats = 0;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }

    }


    return JBPF_CODELET_SUCCESS;
}
