// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "srsran/fapi/messages/dl_tti_request.h"

#include "fapi_gnb_dl_config_stats.pb.h"

#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define MAX_NUM_UE 32


// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(dl_config_stats),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};


// RNTI hashmap, min
DEFINE_PROTOHASH_64(rnti_hash, MAX_NUM_UE)
// Histogram scales
// Power of 2 upper bound of max number of PRBs is 512, and we need to shift to fit in the max size of array l1_dlc_prb_hist
#define PRB_HIST_SHIFT LOG2_OF_POWER_OF_2(512 / ( sizeof(out->stats[0].l1_dlc_prb_hist) / sizeof(out->stats[0].l1_dlc_prb_hist[0]) ))
// #define MAX_PRB_HIST_SIZE (512 >> PRB_HIST_SHIFT) == 8

#define MCS_HIST_SHIFT LOG2_OF_POWER_OF_2(32 / ( sizeof(out->stats[0].l1_dlc_mcs_hist) / sizeof(out->stats[0].l1_dlc_mcs_hist[0]) ))
// #define MAX_MCS_HIST_SIZE (32 >> MCS_HIST_SHIFT) == 8

#define TBS_HIST_SHIFT LOG2_OF_POWER_OF_2(65536 / ( sizeof(out->stats[0].l1_dlc_tbs_hist) / sizeof(out->stats[0].l1_dlc_tbs_hist[0]) ))
// #define MAX_TBS_HIST_SIZE (65536 >> TBS_HIST_SHIFT) == 8

// Here we just ignore >4 antennas since we don't have it in the testbed
#define ANT_HIST_SHIFT 0






//#define DEBUG_PRINT 0

extern "C" SEC("jbpf_ran_layer2")
uint64_t jbpf_main(void *state)
{
    struct jbpf_ran_layer2_ctx *ctx = (jbpf_ran_layer2_ctx *)state;
    uint64_t zero_index = 0;

    const uint8_t* ctx_start = reinterpret_cast<const uint8_t*>(ctx->data);
    const uint8_t* ctx_end = reinterpret_cast<const uint8_t*>(ctx->data_end);

    const srsran::fapi::dl_tti_request_message& msg = *reinterpret_cast<const srsran::fapi::dl_tti_request_message*>(ctx_start);
  
    if (reinterpret_cast<const uint8_t*>(&msg) + sizeof(srsran::fapi::dl_tti_request_message) > ctx_end) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }
  
    if (msg.pdus.size() == 0) {
        return JBPF_CODELET_SUCCESS;
    }

    // We don't want to send anything if no data is collected
    uint32_t *not_empty_hist = (uint32_t*)jbpf_map_lookup_elem(&not_empty, &zero_index);
    if (!not_empty_hist) {
        return JBPF_CODELET_FAILURE;
    }

    // Get stats map buffer to save output across invocations
    dl_config_stats *out = (dl_config_stats*)jbpf_map_lookup_elem(&stats_map, &zero_index);
    if (!out) {
        return JBPF_CODELET_FAILURE;
    }

    // loop through each PDU
    uint8_t num_pdus = msg.pdus.size();
    for (uint8_t pdu=0; pdu<num_pdus; pdu++) {

        if (pdu >= srsran::MAX_DL_PDUS_PER_SLOT) {
            break;
        }

        // process depending on pdu_type
        if (msg.pdus[pdu].pdu_type == srsran::fapi::dl_pdu_type::PDCCH) {
        
            // nothing

        } else if (msg.pdus[pdu].pdu_type == srsran::fapi::dl_pdu_type::PDSCH) {

            uint16_t rnti = (uint16_t)msg.pdus[pdu].pdsch_pdu.rnti;

            if (rnti == 0 || rnti == 65535) continue;

            *not_empty_hist = 1;

            // Find CellID/RNTI index in the hashmap
            int is_new;
            uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, rnti_hash, ctx->cell_id, rnti, is_new);
            if (is_new) {
                out->stats[ind].l1_prb_min = __UINT32_MAX__;
                out->stats[ind].l1_tbs_min = __UINT32_MAX__;
                out->stats[ind].l1_mcs_min = __UINT32_MAX__;
            }

            out->stats[ind].l1_cnt++;

            // get pertinent values
            uint16_t rb_size = msg.pdus[pdu].pdsch_pdu.rb_size;
            uint16_t mcs = 0;
            uint32_t tbs = 0;
            uint32_t total_tx = 0;
            for (int i=0; i<msg.pdus[pdu].pdsch_pdu.cws.size(); i++) {

                if (i >= srsran::fapi::dl_pdsch_pdu::MAX_NUM_CW_PER_PDU) break;

                uint16_t mcs_index = msg.pdus[pdu].pdsch_pdu.cws[i].mcs_index;
                if (mcs_index >= mcs) 
                    mcs = mcs_index;

                uint32_t tb_size = (uint32_t)msg.pdus[pdu].pdsch_pdu.cws[i].tb_size.value();
                total_tx += tb_size;
                if (tb_size >= tbs) 
                    tbs = tb_size;

                //jbpf_printf_debug("mcs: %d\n", mcs);
                //jbpf_printf_debug("tbs: %d\n", tbs);
            }
            uint16_t ant = (uint16_t)msg.pdus[pdu].pdsch_pdu.num_layers;


            ///// PRB histogram
            // Create PRB histogram key
            uint16_t prb = ((uint16_t)rb_size) >> PRB_HIST_SHIFT;
            prb = prb & (sizeof(out->stats[ind].l1_dlc_prb_hist) / sizeof(out->stats[ind].l1_dlc_prb_hist[0]) - 1);
            out->stats[ind].l1_dlc_prb_hist_count = MAX(out->stats[ind].l1_dlc_prb_hist_count, prb+1);
            out->stats[ind].l1_dlc_prb_hist[prb]++;
            out->stats[ind].l1_prb_avg += rb_size;
#ifdef DEBUG_PRINT
            jbpf_printf_debug("Hist PRB: rnti=%d PRB=%d (%d)\n", rnti, rb_size, prb);
#endif
            // Increase min and max
            if (out->stats[ind].l1_prb_min > (uint32_t)(rb_size)) {
                out->stats[ind].l1_prb_min = (uint32_t)(rb_size);
            }
            if (out->stats[ind].l1_prb_max < (uint32_t)(rb_size)) {
                out->stats[ind].l1_prb_max = (uint32_t)(rb_size);
            }
#ifdef DEBUG_PRINT
            // We can print only 3 here
            jbpf_printf_debug("Min/max PRB: rnti=%d min=%d max=%d\n",
                        rnti, out->stats[ind].l1_prb_min, out->stats[ind].l1_prb_max);
#endif
            
            ///// MCS histogram
            // Increase bin count
            uint16_t orig_mcs = mcs;
            mcs = mcs >> MCS_HIST_SHIFT;
            mcs = mcs & (sizeof(out->stats[ind].l1_dlc_mcs_hist) / sizeof(out->stats[ind].l1_dlc_mcs_hist[0]) - 1);
            out->stats[ind].l1_dlc_mcs_hist_count = MAX(out->stats[ind].l1_dlc_mcs_hist_count, mcs+1);
            out->stats[ind].l1_dlc_mcs_hist[mcs]++;
            out->stats[ind].l1_mcs_avg += orig_mcs;
#ifdef DEBUG_PRINT
            // We can print only 3 here
            jbpf_printf_debug("Hist MCS: rnti=%d MCS=%d (%d)\n", rnti, orig_mcs, mcs);
#endif

            // Increase min and max
            if (out->stats[ind].l1_mcs_min > (uint32_t)(orig_mcs)) {
                out->stats[ind].l1_mcs_min = (uint32_t)(orig_mcs);
            }
            if (out->stats[ind].l1_mcs_max < (uint32_t)(orig_mcs)) {
                out->stats[ind].l1_mcs_max = (uint32_t)(orig_mcs);
            }

#ifdef DEBUG_PRINT
            // We can print only 3 here
            //jbpf_printf_debug("Min/max MCS: rnti=%d MCS=%d min=%d max=%d\n",
            //            rnti, (orig_mcs), stats->l1_mcs_min[min_ind].val, stats->l1_mcs_max[max_ind].val);
            jbpf_printf_debug("Min/max MCS: rnti=%d min=%d max=%d\n",
                        rnti, out->stats[ind].l1_mcs_min, out->stats[ind].l1_mcs_max);
#endif

            ///// TBS histogram
            // Create TBS histogram key
            uint16_t orig_tbs = tbs;
            tbs = tbs >> TBS_HIST_SHIFT;
            tbs = tbs & (sizeof(out->stats[ind].l1_dlc_tbs_hist) / sizeof(out->stats[ind].l1_dlc_tbs_hist[0]) - 1);
            out->stats[ind].l1_dlc_tbs_hist_count = MAX(out->stats[ind].l1_dlc_tbs_hist_count, tbs+1);
            out->stats[ind].l1_dlc_tbs_hist[tbs]++;
            out->stats[ind].l1_tbs_avg += orig_tbs;
#ifdef DEBUG_PRINT
            jbpf_printf_debug("Hist TBS: rnti=%d TBS=%d (%d)\n", rnti, orig_tbs, tbs);
#endif

            // Increase min and max
            if (out->stats[ind].l1_tbs_min > (uint32_t)(orig_tbs)) {
                out->stats[ind].l1_tbs_min = (uint32_t)(orig_tbs);
            }
            if (out->stats[ind].l1_tbs_max < (uint32_t)(orig_tbs)) {
                out->stats[ind].l1_tbs_max = (uint32_t)(orig_tbs);
            }
#ifdef DEBUG_PRINT
            jbpf_printf_debug("Min/max TBS: rnti=%d min=%d max=%d\n",
                        rnti, out->stats[ind].l1_tbs_min, out->stats[ind].l1_tbs_max);
#endif

            ///// ANT histogram
            // Create ANT histogram key
            ant = ant >> ANT_HIST_SHIFT;
            ant = ant & (sizeof(out->stats[ind].l1_dlc_ant_hist) / sizeof(out->stats[ind].l1_dlc_ant_hist[0]) - 1);
            out->stats[ind].l1_dlc_ant_hist_count = MAX(out->stats[ind].l1_dlc_ant_hist_count, ant+1);
            out->stats[ind].l1_dlc_ant_hist[ant]++;
            out->stats[ind].l1_ant_avg += ant;
#ifdef DEBUG_PRINT
            // We can print only 3 here
            jbpf_printf_debug("Hist ANT: rnti=%d ANT=%d (%d)\n", rnti, msg.pdus[pdu].pdsch_pdu.num_layers, ant);
#endif
           
            /// Total TX
            out->stats[ind].l1_dlc_tx += total_tx;
#ifdef DEBUG_PRINT
            jbpf_printf_debug("TX cnt: rnti=%d tx=%u B total=%u\n", 
                rnti, total_tx, out->stats[ind].l1_dlc_tx);
#endif
                         
        } else if (msg.pdus[pdu].pdu_type == srsran::fapi::dl_pdu_type::CSI_RS) {

            // nothing

        } else if (msg.pdus[pdu].pdu_type == srsran::fapi::dl_pdu_type::SSB) {

            // nothing

        } else {
            return JBPF_CODELET_FAILURE;
        }

    }

    return JBPF_CODELET_SUCCESS;
}
