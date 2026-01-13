// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "srsran/fapi/messages/crc_indication.h"

#include "fapi_gnb_crc_stats.pb.h"

#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"

#define MAX_NUM_UE 32


struct jbpf_load_map_def SEC("maps") not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(crc_stats),
    .max_entries = 1,
};


// RNTI hashmap, min
DEFINE_PROTOHASH_64(rnti_hash, MAX_NUM_UE)

// Histogram scales
// Power of 2 upper bound of max number of PRBs is 512, and we need to shift to fit in the max size of array l1_crc_ta_hist
#define TA_HIST_SHIFT LOG2_OF_POWER_OF_2(128 / ( sizeof(out->stats[0].l1_crc_ta_hist) / sizeof(out->stats[0].l1_crc_ta_hist[0]) ))
#define SNR_HIST_SHIFT LOG2_OF_POWER_OF_2(32 / ( sizeof(out->stats[0].l1_crc_snr_hist) / sizeof(out->stats[0].l1_crc_snr_hist[0]) ))



//#define DEBUG_PRINT 1

extern "C" SEC("jbpf_ran_layer2")
uint64_t jbpf_main(void *state)
{
    struct jbpf_ran_layer2_ctx *ctx = (jbpf_ran_layer2_ctx *)state;
    uint64_t zero_index = 0;

    const uint8_t* ctx_start = reinterpret_cast<const uint8_t*>(ctx->data);
    const uint8_t* ctx_end = reinterpret_cast<const uint8_t*>(ctx->data_end);

    const srsran::fapi::crc_indication_message& msg = *reinterpret_cast<const srsran::fapi::crc_indication_message*>(ctx_start);
    
    if (reinterpret_cast<const uint8_t*>(&msg) + sizeof(srsran::fapi::crc_indication_message) > ctx_end) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }
    
    if (msg.pdus.size() == 0) {
        return JBPF_CODELET_SUCCESS;
    }

    uint32_t *not_empty_hist = (uint32_t*)jbpf_map_lookup_elem(&not_empty, &zero_index);
    if (!not_empty_hist) {
        return JBPF_CODELET_FAILURE;
    }

    // Get stats map buffer to save output across invocations
    crc_stats *out = (crc_stats *)jbpf_map_lookup_elem(&stats_map, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;
    
    // loop through each PDU
    for (const auto& fapi_pdu : msg.pdus) {

        uint32_t rnti = (uint32_t)fapi_pdu.rnti;

        if (rnti != 0 && rnti != 65535) {
            *not_empty_hist = 1;
            
            // Find RNTI index in the hashmap
            int is_new;

            // Find RNTI index in the hashmap
            uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, rnti_hash, ctx->cell_id, rnti, is_new);
            if (is_new) {
              out->stats[ind].l1_ta_min = __UINT32_MAX__;
              out->stats[ind].l1_snr_min = __UINT32_MAX__;
            }

            ///// TA histogram
            // Create TA histogram key

            uint16_t nta = (uint16_t) ((fapi_pdu.timing_advance_offset_ns >= 0) ?
              (fapi_pdu.timing_advance_offset_ns >> 5) : (-fapi_pdu.timing_advance_offset_ns >> 5));

            uint8_t ta = (uint8_t)(nta) >> TA_HIST_SHIFT;
            ta = ta & (sizeof(out->stats[ind].l1_crc_ta_hist) / sizeof(out->stats[ind].l1_crc_ta_hist[0]) - 1);
            out->stats[ind].l1_crc_ta_hist_count = MAX(out->stats[ind].l1_crc_ta_hist_count, ta+1);
            out->stats[ind].l1_crc_ta_hist[ta]++;

#ifdef DEBUG_PRINT
            jbpf_printf_debug("Hist TA: rnti=%d TA=%d cnt=%d\n", 
              rnti, nta, out->stats[ind].l1_crc_ta_hist[ta]);
#endif

            // Increase min and max
            if (out->stats[ind].l1_ta_min > (uint32_t)(nta)) {
                out->stats[ind].l1_ta_min = (uint32_t)(nta);
            }
            if (out->stats[ind].l1_ta_max < (uint32_t)(nta)) {
                out->stats[ind].l1_ta_max = (uint32_t)(nta);
            }
#ifdef DEBUG_PRINT
            jbpf_printf_debug("Min/max TA: rnti=%d min=%d max=%d\n",
                        rnti, out->stats[ind].l1_ta_min, out->stats[ind].l1_ta_max);
#endif

            ///// SNR histogram
            // Create SNR histogram key
            uint16_t snr = (uint16_t)((fapi_pdu.ul_sinr_metric + 32768 ) >> 8);
            uint16_t orig_snr = snr;

            // Increase bin count
            snr = orig_snr >> SNR_HIST_SHIFT;
            snr = snr & (sizeof(out->stats[ind].l1_crc_snr_hist) / sizeof(out->stats[ind].l1_crc_snr_hist[0]) - 1);
            out->stats[ind].l1_crc_snr_hist_count = MAX(out->stats[ind].l1_crc_snr_hist_count, snr+1);
            out->stats[ind].l1_crc_snr_hist[snr]++;
#ifdef DEBUG_PRINT
            jbpf_printf_debug("Hist SNR: rnti=%d snr=%d cnt=%d\n", 
                rnti, orig_snr, out->stats[ind].l1_crc_snr_hist[snr]);
#endif      

            // Increase min and max
            if (out->stats[ind].l1_snr_min > (uint32_t)(orig_snr)) {
                out->stats[ind].l1_snr_min = (uint32_t)(orig_snr);
            }
            if (out->stats[ind].l1_snr_max < (uint32_t)(orig_snr)) {
                out->stats[ind].l1_snr_max = (uint32_t)(orig_snr);
            }
#ifdef DEBUG_PRINT
            jbpf_printf_debug("Min/max SNR: rnti=%d min=%d max=%d\n",
                        rnti, out->stats[ind].l1_snr_min, out->stats[ind].l1_snr_max);
#endif    
        }
    }

    return JBPF_CODELET_SUCCESS;
}
