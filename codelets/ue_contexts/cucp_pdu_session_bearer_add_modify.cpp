// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.
//
// This codelet simply forwards the message.
//


#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "ue_contexts.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"

#include "jbpf_defs.h"
#include "jbpf_helper.h"

// output map for stats
jbpf_ringbuf_map(output_map, cucp_pdu_session_bearer_add_modify, 256);

// map to store data before sending to output_map
struct jbpf_load_map_def SEC("maps") output_tmp_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(cucp_pdu_session_bearer_add_modify),
    .max_entries = 1,
};

//#define DEBUG_PRINT

extern "C" SEC("jbpf_srsran_generic")
uint64_t jbpf_main(void* state)
{
    struct jbpf_ran_generic_ctx *ctx = (jbpf_ran_generic_ctx *)state;

    const jbpf_pdu_session_ctx_info& session_ctx = *reinterpret_cast<const jbpf_pdu_session_ctx_info*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&session_ctx) + sizeof(jbpf_pdu_session_ctx_info) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    // get the output map
    int zero_index=0;
    cucp_pdu_session_bearer_add_modify *out = (cucp_pdu_session_bearer_add_modify *)jbpf_map_lookup_elem(&output_tmp_map, &zero_index);
    if (!out) {
        return JBPF_CODELET_FAILURE;    
    }

    // populate the output
    uint64_t timestamp = jbpf_time_get_ns();
    out->timestamp = timestamp;
    out->cucp_ue_index = session_ctx.cu_up_ue_index;
    out->pdu_session_id = session_ctx.pdu_session_id;
    out->drb_id = session_ctx.drb_id;
    out->nssai.sst = session_ctx.nssai.sst;
    out->nssai.sd = session_ctx.nssai.sd;

    int ret = jbpf_ringbuf_output(&output_map, (void *)out, sizeof(cucp_pdu_session_bearer_add_modify));

    if (ret < 0) {
#ifdef DEBUG_PRINT
        jbpf_printf_debug("cucp_pdu_session_bearer: Failure: jbpf_ringbuf_output\n");
#endif
        return JBPF_CODELET_FAILURE;
    }

    return JBPF_CODELET_SUCCESS;
}

