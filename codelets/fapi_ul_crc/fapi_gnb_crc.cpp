// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "srsran/fapi/messages/crc_indication.h"

#include "fapi_gnb_crc.pb.h"

#include "../utils/misc_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#define MAX_NUM_UE (32)

jbpf_ringbuf_map(output_map, crc_stats, 256);

struct jbpf_load_map_def SEC("maps") output_map_tmp = {
  .type = JBPF_MAP_TYPE_ARRAY,
  .key_size = sizeof(int),
  .value_size = sizeof(crc_stats),
  .max_entries = 1,
};


//#define DEBUG_PRINT

extern "C" SEC("jbpf_ran_layer2")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_ran_layer2_ctx *ctx = (jbpf_ran_layer2_ctx *)state;

    const srsran::fapi::crc_indication_message& msg = *reinterpret_cast<const srsran::fapi::crc_indication_message*>(ctx->data);
    
    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&msg) + sizeof(srsran::fapi::crc_indication_message) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    crc_stats *out = (crc_stats *)jbpf_map_lookup_elem(&output_map_tmp, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;
    
    out->timestamp = jbpf_time_get_ns();
    out->stats_count = 0;

    for (const auto& fapi_pdu : msg.pdus) {
        if (out->stats_count >= MAX_NUM_UE) {
            break;
        }
        out->stats[out->stats_count & MAX_NUM_UE].rnti = static_cast<unsigned int>(fapi_pdu.rnti);
        out->stats[out->stats_count & MAX_NUM_UE].ta = static_cast<unsigned int>(fapi_pdu.timing_advance_offset_ns);
        out->stats[out->stats_count & MAX_NUM_UE].snr = static_cast<unsigned int>(fapi_pdu.ul_sinr_metric);
        out->stats_count++;
    }

    if ((out->stats_count > 0) && (out->stats_count <= MAX_NUM_UE)) {
        int ret = jbpf_ringbuf_output(&output_map, (void *)out, sizeof(crc_stats));
        jbpf_map_clear(&output_map_tmp);
        if (ret < 0) {
#ifdef DEBUG_PRINT
            jbpf_printf_debug("fapi_gnb_crc: Failure: jbpf_ringbuf_output\n");
#endif
            return JBPF_CODELET_FAILURE;
        }
    }

    return JBPF_CODELET_SUCCESS;
}
