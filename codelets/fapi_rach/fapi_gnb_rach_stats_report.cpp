// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "fapi_gnb_rach_stats.pb.h"

#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


jbpf_ringbuf_map(output_map, rach_stats, 1000);

struct jbpf_load_map_def SEC("maps") not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") last_time = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint64_t),
    .max_entries = 1,
};

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(rach_stats),
    .max_entries = 1,
};

// The same as in fapi_gnb_rach_stats.options
#define MAX_TA_HIST_SIZE 64
#define MAX_PWR_HIST_SIZE 32

DEFINE_PROTOHASH_32(hist_TA, MAX_TA_HIST_SIZE);
DEFINE_PROTOHASH_32(hist_PWR, MAX_PWR_HIST_SIZE);


//#define DEBUG_PRINT 1

extern "C" SEC("jbpf_ran_layer2")
uint64_t jbpf_main(void *state)
{
    struct jbpf_stats_ctx *ctx;
    uint64_t zero_index = 0;
    uint64_t timestamp;

    ctx = (struct jbpf_stats_ctx *)state;

  // We don't want to send anything if no data is collected
    uint32_t *not_empty_hist = (uint32_t*)jbpf_map_lookup_elem(&not_empty, &zero_index);
    if (!not_empty_hist)
        return JBPF_CODELET_FAILURE;

    // Get stats map buffer to save output across invocations
    void *c = jbpf_map_lookup_elem(&stats_map, &zero_index);
    if (!c)
        return 1;
    rach_stats *out = (rach_stats *)c;

    // Timestamp field name should not change as it is hardcoded in post processing
    timestamp = jbpf_time_get_ns();

    uint64_t timestamp32 = (uint64_t) (timestamp >> 30);

    uint64_t lt_index = 0;
    uint64_t *last_timestamp = (uint64_t*)jbpf_map_lookup_elem(&last_time, &lt_index);
    if (!last_timestamp)
        return JBPF_CODELET_FAILURE;

#ifdef DEBUG_PRINT
    jbpf_printf_debug("OUTPUT CHECK: timestamp=%lu timestamp32=%lu last_timestamp=%u \n", timestamp, timestamp32, *last_timestamp);
#endif

    if (*not_empty_hist && *last_timestamp < timestamp32)
    {
        out->timestamp = timestamp;

#ifdef DEBUG_PRINT
          jbpf_printf_debug("OUTPUT: %lu\n", out->timestamp);
#endif

      int ret = jbpf_ringbuf_output(&output_map, (void *) out, sizeof(rach_stats));

      JBPF_HASHMAP_CLEAR(&hist_TA);
      JBPF_HASHMAP_CLEAR(&hist_PWR);

      // Reset the info
      // NOTE: this is not thread safe, but we don't care here
      // The worst case we can overwrite someone else writing
      jbpf_map_clear(&stats_map);

      *not_empty_hist = 0;
      *last_timestamp = timestamp32;

      if (ret < 0) {
#ifdef DEBUG_PRINT
          jbpf_printf_debug("fapi_gnb_rach_stats_report: Failure: jbpf_ringbuf_output\n");
#endif
          return JBPF_CODELET_FAILURE;
      }

    } else {
#ifdef DEBUG_PRINT
        jbpf_printf_debug("OUTPUT NOT SENT: timestamp=%lu not_empty_hist=%lu\n", 
          out->timestamp, *not_empty_hist);
#endif
    }

    return JBPF_CODELET_SUCCESS;
}
