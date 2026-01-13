// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "srsran/fapi/messages/rach_indication.h"

#include "fapi_gnb_rach_stats.pb.h"

#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


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
    .value_size = sizeof(rach_stats),
    .max_entries = 1,
};


// The same as in fapi_gnb_rach_stats.options
#define MAX_TA_HIST_SIZE 64
#define MAX_PWR_HIST_SIZE 32

DEFINE_PROTOHASH_32(hist_TA, MAX_TA_HIST_SIZE);
DEFINE_PROTOHASH_32(hist_PWR, MAX_PWR_HIST_SIZE);


// TA Histogram (According to 3GPP, this is can be 0-3846)
#define TA_HIST_SHIFT LOG2_OF_POWER_OF_2(4096 / ( sizeof(out->l1_rach_ta_hist) / sizeof(out->l1_rach_ta_hist[0]) ))

// Power Histogram
#define PWR_HIST_SHIFT LOG2_OF_POWER_OF_2(32 / ( sizeof(out->l1_rach_pwr_hist) / sizeof(out->l1_rach_pwr_hist[0]) ))





//#define DEBUG_PRINT 1

extern "C" SEC("jbpf_ran_layer2")
uint64_t jbpf_main(void *state)
{
    struct jbpf_ran_layer2_ctx *ctx = (jbpf_ran_layer2_ctx *)state;
    uint64_t zero_index = 0;

    const uint8_t* ctx_start = reinterpret_cast<const uint8_t*>(ctx->data);
    const uint8_t* ctx_end = reinterpret_cast<const uint8_t*>(ctx->data_end);

    const srsran::fapi::rach_indication_message& msg = *reinterpret_cast<const srsran::fapi::rach_indication_message*>(ctx_start);
  
    if (reinterpret_cast<const uint8_t*>(&msg) + sizeof(srsran::fapi::rach_indication_message) > ctx_end) {
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
    rach_stats *out = (rach_stats *)jbpf_map_lookup_elem(&stats_map, &zero_index);
    if (!out) {
        return JBPF_CODELET_FAILURE;
    }
  
    // loop through each PDU
    uint8_t num_pdus = msg.pdus.size();
    for (uint8_t pdu=0; pdu<num_pdus; pdu++) {

        if (pdu >= srsran::fapi::rach_indication_message::MAX_NUM_RACH_PDUS) {
            break;
        }

        // loop through each preamble
        int num_preambles = msg.pdus[pdu].preambles.size();
        for (uint8_t preamble=0; preamble<num_preambles; preamble++) {

            if (preamble >= srsran::fapi::rach_indication_pdu::MAX_NUM_PREAMBLES) {
                 break;
            }

             *not_empty_hist = 1;
    
            ///// TA histogram
            // Create TA histogram key
            uint32_t ta = msg.pdus[pdu].preambles[preamble].timing_advance_offset_ns;
            JBPF_HIST_BIN(ta, MAX_TA_HIST_SIZE, TA_HIST_SHIFT);

            //Increase bin count
            int is_new;
            uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(out, l1_rach_ta_hist, hist_TA, ta, is_new);
            if (is_new) out->l1_rach_ta_hist[ind].cnt = 0;
            out->l1_rach_ta_hist[ind].cnt++; 
#ifdef DEBUG_PRINT
            jbpf_printf_debug("Hist TA: TA=%d key=%d cnt=%d\n", 
                pdu_data->nTa, ta, out->l1_rach_ta_hist[ind].cnt);
#endif

            ///// PWR histogram
            // Create PWR histogram key
            // Approximately as defined: 0->170000, 0.001 dB step, -140 to 30 dBm
            int32_t pwr = (int32_t)((msg.pdus[pdu].preambles[preamble].preamble_pwr >> 10) - 140);
            int32_t key = pwr;
            JBPF_HIST_BIN(key, MAX_PWR_HIST_SIZE, PWR_HIST_SHIFT);

            // Increase bin count
            ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(out, l1_rach_pwr_hist, hist_PWR, pwr, is_new);
            if (is_new) out->l1_rach_pwr_hist[ind].cnt = 0;
            out->l1_rach_pwr_hist[ind].cnt++; 
#ifdef DEBUG_PRINT
            jbpf_printf_debug("Hist PWR: snr=%d key=%d cnt=%d\n", 
                pwr, key, out->l1_rach_pwr_hist[ind].cnt);
#endif
        }
    }

    return JBPF_CODELET_SUCCESS;
}
