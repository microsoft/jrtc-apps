//ontainers/Docker/srsRAN_Project Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "srsran/scheduler/scheduler_feedback_handler.h"

#include "mac_helpers.h"
#include "mac_sched_uci_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"



#include "jbpf_defs.h"
#include "jbpf_helper.h"
#include "jbpf_helper_utils.h"
#include "../utils/stats_utils.h"


struct jbpf_load_map_def SEC("maps") uci_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
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




//#define DEBUG_PRINT

extern "C" SEC("jbpf_ran_mac_sched")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_mac_sched_ctx *ctx = (jbpf_mac_sched_ctx *)state;
    
    const srsran::uci_indication::uci_pdu& uci_pdu = *reinterpret_cast<const srsran::uci_indication::uci_pdu*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&uci_pdu) + sizeof(srsran::uci_indication::uci_pdu) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&uci_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    uci_stats *out = (uci_stats *)jbpf_map_lookup_elem(&stats_map_uci, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;

    int new_val = 0;

    // Increase loss count
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_32(out, stats, uci_hash, uci_pdu.ue_index, new_val);
    if (new_val) {
        out->stats[ind % MAX_NUM_UE].du_ue_index = uci_pdu.ue_index;
        out->stats[ind % MAX_NUM_UE].sr_detected = 0;
        out->stats[ind % MAX_NUM_UE].time_advance_offset.count = 0;
        out->stats[ind % MAX_NUM_UE].time_advance_offset.total = 0;
        out->stats[ind % MAX_NUM_UE].time_advance_offset.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE].time_advance_offset.max = 0;
        out->stats[ind % MAX_NUM_UE].has_time_advance_offset = false;
        out->stats[ind % MAX_NUM_UE].csi.ri.count = 0;
        out->stats[ind % MAX_NUM_UE].csi.ri.total = 0;
        out->stats[ind % MAX_NUM_UE].csi.ri.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE].csi.ri.max = 0;
        out->stats[ind % MAX_NUM_UE].csi.has_ri = false;
        out->stats[ind % MAX_NUM_UE].csi.cqi.count = 0;
        out->stats[ind % MAX_NUM_UE].csi.cqi.total = 0;
        out->stats[ind % MAX_NUM_UE].csi.cqi.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE].csi.cqi.max = 0;
        out->stats[ind % MAX_NUM_UE].csi.has_cqi = false;
        out->stats[ind % MAX_NUM_UE].has_csi = false;
    }

    if (const auto* pucch_f0f1 = std::get_if<srsran::uci_indication::uci_pdu::uci_pucch_f0_or_f1_pdu>(&uci_pdu.pdu)) {

        // process uci_pucch_f0_or_f1_pdu

        // sr_detected
        if (pucch_f0f1->sr_detected) {
            out->stats[ind % MAX_NUM_UE].sr_detected++;
        } 
        
        // harqs
        // The harqs are nort read here as they could gove misleading results.
        // For correct HARQ ACK, yuse the mac_sched_dl_harq_stst.cpp codelet.

        // timing advance
        const bool is_uci_valid = not pucch_f0f1->harqs.empty() or pucch_f0f1->sr_detected;
        if (is_uci_valid and pucch_f0f1->time_advance_offset.has_value() and pucch_f0f1->ul_sinr_dB.has_value()) {

            // Cant handle SINR as it is floating point

            // // timing advance offset
            STATS_UPDATE(out->stats[ind % MAX_NUM_UE].time_advance_offset, static_cast<uint64_t>(pucch_f0f1->time_advance_offset->to_Tc()));
            out->stats[ind % MAX_NUM_UE].has_time_advance_offset = true;
        }

    } else if (const auto* pusch_pdu = std::get_if<srsran::uci_indication::uci_pdu::uci_pusch_pdu>(&uci_pdu.pdu)) {

        // harqs
        // The harqs are nort read here as they could gove misleading results.
        // For correct HARQ ACK, yuse the mac_sched_dl_harq_stst.cpp codelet.

        // csi
        if (pusch_pdu->csi.has_value()) {

            // ri   
            if (pusch_pdu->csi->ri.has_value()) {
                STATS_UPDATE(out->stats[ind % MAX_NUM_UE].csi.ri, static_cast<uint32_t>(static_cast<uint8_t>(pusch_pdu->csi->ri.value())));
                out->stats[ind % MAX_NUM_UE].csi.has_ri = true;
            }

            // first_tb_wideband_cqi
            if (pusch_pdu->csi->first_tb_wideband_cqi.has_value()) {
                STATS_UPDATE(out->stats[ind % MAX_NUM_UE].csi.cqi, static_cast<uint32_t>(static_cast<uint8_t>(pusch_pdu->csi->first_tb_wideband_cqi.value())));
                out->stats[ind % MAX_NUM_UE].csi.has_cqi = true;
            }
            // second_tb_wideband_cqi
            if (pusch_pdu->csi->second_tb_wideband_cqi.has_value()) {
                STATS_UPDATE(out->stats[ind % MAX_NUM_UE].csi.cqi, static_cast<uint32_t>(static_cast<uint8_t>(pusch_pdu->csi->second_tb_wideband_cqi.value())));
                out->stats[ind % MAX_NUM_UE].csi.has_cqi = true;
            }
            
            out->stats[ind % MAX_NUM_UE].has_csi = true;
        }

    } else if (const auto* pucch_f2f3f4 = std::get_if<srsran::uci_indication::uci_pdu::uci_pucch_f2_or_f3_or_f4_pdu>(&uci_pdu.pdu)) {

        // sr bits
        const size_t sr_bit_position_with_1_sr_bit = 0;
        if (not pucch_f2f3f4->sr_info.empty() and pucch_f2f3f4->sr_info.test(sr_bit_position_with_1_sr_bit)) {
           
            // Handle SR indication.
            out->stats[ind % MAX_NUM_UE].sr_detected++;
        }   

        // harqs
        // The harqs are nort read here as they could gove misleading results.
        // For correct HARQ ACK, yuse the mac_sched_dl_harq_stst.cpp codelet.

        // csi
        if (pucch_f2f3f4->csi.has_value()) {

            // ri
            if (pucch_f2f3f4->csi->ri.has_value()) {
                STATS_UPDATE(out->stats[ind % MAX_NUM_UE].csi.ri, static_cast<uint32_t>(static_cast<uint8_t>(pucch_f2f3f4->csi->ri.value())));
                out->stats[ind % MAX_NUM_UE].csi.has_ri = true;
            }

            // first_tb_wideband_cqi
            if (pucch_f2f3f4->csi->first_tb_wideband_cqi.has_value()) {
                STATS_UPDATE(out->stats[ind % MAX_NUM_UE].csi.cqi, static_cast<uint32_t>(static_cast<uint8_t>(pucch_f2f3f4->csi->first_tb_wideband_cqi.value())));
                out->stats[ind % MAX_NUM_UE].csi.has_cqi = true;
            }
            // second_tb_wideband_cqi
            if (pucch_f2f3f4->csi->second_tb_wideband_cqi.has_value()) {
                STATS_UPDATE(out->stats[ind % MAX_NUM_UE].csi.cqi, static_cast<uint32_t>(static_cast<uint8_t>(pucch_f2f3f4->csi->second_tb_wideband_cqi.value())));
                out->stats[ind % MAX_NUM_UE].csi.has_cqi = true;
            }
            
            out->stats[ind % MAX_NUM_UE].has_csi = true;
        }

        // timing advance
        const bool is_uci_valid =
            //not pucch_f2f3f4->harqs.empty() or
            (not pucch_f2f3f4->sr_info.empty() and pucch_f2f3f4->sr_info.test(sr_bit_position_with_1_sr_bit)) or
            pucch_f2f3f4->csi.has_value();

        // Process Timing Advance Offset.
        if (is_uci_valid and pucch_f2f3f4->time_advance_offset.has_value() and
            pucch_f2f3f4->ul_sinr_dB.has_value()) {

            // Handle UL SINR and Timing Advance Offset
            STATS_UPDATE(out->stats[ind % MAX_NUM_UE].time_advance_offset, static_cast<uint64_t>(pucch_f2f3f4->time_advance_offset->to_Tc()));
            out->stats[ind % MAX_NUM_UE].has_time_advance_offset = true;
        }

    } else {
        // jbpf_printf_debug("Unknown UCI PDU type\n");
        return JBPF_CODELET_FAILURE;
    }
    
    *not_empty_stats = 1;

    return JBPF_CODELET_SUCCESS;
}
