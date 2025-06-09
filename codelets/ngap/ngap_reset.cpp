// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "ngap.pb.h"

#include "../utils/misc_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#define MAX_NUM_UE (32)

jbpf_ringbuf_map(output_map, ngap_reset, 256);

struct jbpf_load_map_def SEC("maps") output_map_tmp = {
  .type = JBPF_MAP_TYPE_ARRAY,
  .key_size = sizeof(int),
  .value_size = sizeof(ngap_reset),
  .max_entries = 1,
};


//#define DEBUG_PRINT

extern "C" SEC("jbpf_srsran_generic")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_ran_generic_ctx *ctx = (jbpf_ran_generic_ctx *)state;
    
    const jbpf_ngap_ctx_info& ngap_ctx = *reinterpret_cast<const jbpf_ngap_ctx_info*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&ngap_ctx) + sizeof(jbpf_ngap_ctx_info) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    ngap_reset *out = (ngap_reset *)jbpf_map_lookup_elem(&output_map_tmp, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;

    out->timestamp = jbpf_time_get_ns();

    if ((ngap_ctx.ran_ue_ngap_id_set) || (ngap_ctx.amf_ue_ngap_id_set)) {
        if (ngap_ctx.ran_ue_ngap_id_set) {
            out->ue_ctx.ran_ue_id = ngap_ctx.ran_ue_ngap_id;
        }
        if (ngap_ctx.amf_ue_ngap_id_set) {
            out->ue_ctx.amf_ue_id = ngap_ctx.amf_ue_ngap_id;
        }
    }

    int ret = jbpf_ringbuf_output(&output_map, (void *)out, sizeof(ngap_reset));
    jbpf_map_clear(&output_map_tmp);
    if (ret < 0) {
#ifdef DEBUG_PRINT
        jbpf_printf_debug("ngap_reset: Failure: jbpf_ringbuf_output\n");
#endif
        return JBPF_CODELET_FAILURE;
    }

    return JBPF_CODELET_SUCCESS;
}
