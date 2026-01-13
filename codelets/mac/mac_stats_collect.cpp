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


//// CRC

jbpf_ringbuf_map(output_map_crc, crc_stats, 1000);

struct jbpf_load_map_def SEC("maps") last_time_crc = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint64_t),
    .max_entries = 1,
};

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_crc = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(crc_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_32(crc_hash, MAX_NUM_UE);

struct jbpf_load_map_def SEC("maps") crc_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};



//// BSR

jbpf_ringbuf_map(output_map_bsr, bsr_stats, 1000);

struct jbpf_load_map_def SEC("maps") last_time_bsr = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint64_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_bsr = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(bsr_stats),
    .max_entries = 1,
  };
  
DEFINE_PROTOHASH_32(bsr_hash, MAX_NUM_UE);

struct jbpf_load_map_def SEC("maps") bsr_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};



//// PHR

jbpf_ringbuf_map(output_map_phr, phr_stats, 1000);

struct jbpf_load_map_def SEC("maps") last_time_phr = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint64_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") phr_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_phr = {
  .type = JBPF_MAP_TYPE_ARRAY,
  .key_size = sizeof(int),
  .value_size = sizeof(phr_stats),
  .max_entries = 1,
};

DEFINE_PROTOHASH_64(phr_hash, MAX_NUM_UE_CELL);


//// UCI

jbpf_ringbuf_map(output_map_uci, uci_stats, 1000);

struct jbpf_load_map_def SEC("maps") last_time_uci = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint64_t),
    .max_entries = 1,
};

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_uci = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uci_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_32(uci_hash, MAX_NUM_UE);

struct jbpf_load_map_def SEC("maps") uci_not_empty = {
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
    ///// CRC stats

    uint32_t *not_empty_crc_stats = (uint32_t*)jbpf_map_lookup_elem(&crc_not_empty, &zero_index);
    if (!not_empty_crc_stats)
        return JBPF_CODELET_FAILURE;

    // Get stats map buffer to save output across invocations
    void *c = jbpf_map_lookup_elem(&stats_map_crc, &zero_index);
    if (!c)
        return JBPF_CODELET_FAILURE;
    crc_stats *out_crc = (crc_stats *)c;

    uint64_t *last_timestamp_crc = (uint64_t*)jbpf_map_lookup_elem(&last_time_crc, &zero_index);
    if (!last_timestamp_crc)
        return JBPF_CODELET_FAILURE;

        
    if (*not_empty_crc_stats && *last_timestamp_crc < timestamp32)
    {
        out_crc->timestamp = timestamp;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("CRC OUTPUT: %lu\n", out_crc->timestamp);
#endif

        int ret = jbpf_ringbuf_output(&output_map_crc, (void *) out_crc, sizeof(crc_stats));

        JBPF_HASHMAP_CLEAR(&crc_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_crc);

        *not_empty_crc_stats = 0;
        *last_timestamp_crc = timestamp32;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }
    }




    ////////////////////////////////////////////////////////////////////////////////
    ///// BSR stats

    uint32_t *not_empty_bsr_stats = (uint32_t*)jbpf_map_lookup_elem(&bsr_not_empty, &zero_index);
    if (!not_empty_bsr_stats) {
        return JBPF_CODELET_FAILURE;
    }

    bsr_stats *out_bsr = (bsr_stats *)jbpf_map_lookup_elem(&stats_map_bsr, &zero_index);
    if (!out_bsr)
        return JBPF_CODELET_FAILURE;

    uint64_t *last_timestamp_bsr = (uint64_t*)jbpf_map_lookup_elem(&last_time_bsr, &zero_index);
    if (!last_timestamp_bsr)
        return JBPF_CODELET_FAILURE;
    

    if (*not_empty_bsr_stats && *last_timestamp_bsr < timestamp32)
    {
        out_bsr->timestamp = timestamp;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("BSR OUTPUT: %lu\n", out_bsr->timestamp);
#endif

        int ret = jbpf_ringbuf_output(&output_map_bsr, (void *) out_bsr, sizeof(bsr_stats));

        JBPF_HASHMAP_CLEAR(&bsr_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_bsr);

        *not_empty_bsr_stats = 0;
        *last_timestamp_bsr = timestamp32;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }

    }



    ////////////////////////////////////////////////////////////////////////////////
    ///// PHR stats

    uint32_t *not_empty_phr_stats = (uint32_t*)jbpf_map_lookup_elem(&phr_not_empty, &zero_index);
    if (!not_empty_phr_stats) {
        return JBPF_CODELET_FAILURE;
    }

    phr_stats *out_phr = (phr_stats *)jbpf_map_lookup_elem(&stats_map_phr, &zero_index);
    if (!out_phr)
        return JBPF_CODELET_FAILURE;

    uint64_t *last_timestamp_phr = (uint64_t*)jbpf_map_lookup_elem(&last_time_phr, &zero_index);
    if (!last_timestamp_phr)
        return JBPF_CODELET_FAILURE;
    

    if (*not_empty_phr_stats && *last_timestamp_phr < timestamp32)
    {
        out_phr->timestamp = timestamp;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("PHR OUTPUT: %lu\n", out_phr->timestamp);
#endif

        int ret = jbpf_ringbuf_output(&output_map_phr, (void *) out_phr, sizeof(phr_stats));

        JBPF_HASHMAP_CLEAR(&phr_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_phr);

        *not_empty_phr_stats = 0;
        *last_timestamp_phr = timestamp32;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }
    }


    ////////////////////////////////////////////////////////////////////////////////
    ///// UCI stats

    uint32_t *not_empty_uci_stats = (uint32_t*)jbpf_map_lookup_elem(&uci_not_empty, &zero_index);
    if (!not_empty_uci_stats)
        return JBPF_CODELET_FAILURE;

    // Get stats map buffer to save output across invocations
    c = jbpf_map_lookup_elem(&stats_map_uci, &zero_index);
    if (!c)
        return JBPF_CODELET_FAILURE;
    uci_stats *out_uci = (uci_stats *)c;

    uint64_t *last_timestamp_uci = (uint64_t*)jbpf_map_lookup_elem(&last_time_uci, &zero_index);
    if (!last_timestamp_uci)
        return JBPF_CODELET_FAILURE;

        
    if (*not_empty_uci_stats && *last_timestamp_uci < timestamp32)
    {
        out_uci->timestamp = timestamp;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("CRC OUTPUT: %lu\n", out_uci->timestamp);
#endif

        int ret = jbpf_ringbuf_output(&output_map_uci, (void *) out_uci, sizeof(uci_stats));

        JBPF_HASHMAP_CLEAR(&uci_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_uci);

        *not_empty_uci_stats = 0;
        *last_timestamp_uci = timestamp32;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }
    }    

    return JBPF_CODELET_SUCCESS;
}
