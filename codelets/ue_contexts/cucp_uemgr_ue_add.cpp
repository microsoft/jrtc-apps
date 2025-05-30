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
jbpf_ringbuf_map(output_map, cucp_ue_ctx_creation, 256);

// map to store data before sending to output_map
struct jbpf_load_map_def SEC("maps") output_tmp_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(cucp_ue_ctx_creation),
    .max_entries = 1,
};

//#define DEBUG_PRINT

extern "C" SEC("jbpf_srsran_generic")
uint64_t jbpf_main(void* state)
{
    struct jbpf_ran_generic_ctx *ctx = (jbpf_ran_generic_ctx *)state;

    const jbpf_cucp_uemgr_ctx_info& cucp_ctx = *reinterpret_cast<const jbpf_cucp_uemgr_ctx_info*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&cucp_ctx) + sizeof(jbpf_cucp_uemgr_ctx_info) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    // get the output map
    int zero_index=0;
    cucp_ue_ctx_creation *out = (cucp_ue_ctx_creation *)jbpf_map_lookup_elem(&output_tmp_map, &zero_index);
    if (!out) {
        return JBPF_CODELET_FAILURE;    
    }

    uint32_t pci_set = (uint32_t) (ctx->srs_meta_data1 >> 16);
    uint32_t pci = (uint32_t) (ctx->srs_meta_data1 & 0xFFFF);
    uint32_t crnti_set = (uint32_t) (ctx->srs_meta_data2 >> 16);
    uint32_t crnti = (uint32_t) (ctx->srs_meta_data2 & 0xFFFF);

    // populate the output
    uint64_t timestamp = jbpf_time_get_ns();
    out->timestamp = timestamp;
    out->cucp_ue_index = cucp_ctx.cu_cp_ue_index;
    out->plmn = cucp_ctx.plmn;
    out->has_pci = (pci_set != 0);
    out->pci = pci;
    out->has_crnti = (crnti_set != 0);
    out->crnti = crnti;
        
    int ret = jbpf_ringbuf_output(&output_map, (void *)out, sizeof(cucp_ue_ctx_creation));
    
    if (ret < 0) {
#ifdef DEBUG_PRINT
        jbpf_printf_debug("cucp_ue_ctx_creation: Failure: jbpf_ringbuf_output\n");
#endif
        return JBPF_CODELET_FAILURE;
    }

    return JBPF_CODELET_SUCCESS;
}

