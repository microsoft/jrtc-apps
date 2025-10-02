// Copyright (c) Microsoft Corporation. All rights reserved.
/*
This codelet allows an app to configure the allocations of slices.
*/

#include <linux/bpf.h>

#include <string.h>

#include "jbpf_srsran_contexts.h"
#include "slice_mgmt.pb.h"

#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#include "../utils/misc_utils.h"



// The input request channel
jbpf_control_input_map(slice_request_map, slice_mgmt_req, 1);

//  Temporary map to store an incoming request.  Used as stack is too small for a local variable.
struct jbpf_load_map_def SEC("maps") input_request_tmp = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(slice_mgmt_req),
    .max_entries = 1,
};

typedef struct {
    int requested;
    slice_mgmt_set_req request;
} slice_mgmt_set_request_t;

// Map to store "SET" requests.  This is maintained as the request might be for a specific sfn/sn
struct jbpf_load_map_def SEC("maps") set_request_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(slice_mgmt_set_request_t),
    .max_entries = 1,
};

 // Flag to indicate if an INDICATION needs to be sent to higher layers
struct jbpf_load_map_def SEC("maps") indication_trigger_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

// Latest config sent back to the app
jbpf_output_map(slice_indication_map, slice_mgmt_ind, 16);



extern "C" SEC("jbpf_srsran_generic")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;

    int i=0;
    int j=0;

    struct jbpf_ran_generic_ctx* ctx = (jbpf_ran_generic_ctx*)state;

    jbpf_slice_allocation& data = *reinterpret_cast<jbpf_slice_allocation*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&data) + sizeof(jbpf_slice_allocation) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    // get sfn and slot_index from metadata
    uint32_t sfn = (uint32_t) (ctx->srs_meta_data1 >> 16) & 0xFFFF;   
    uint32_t slot_index = (uint32_t) (ctx->srs_meta_data1 & 0xFFFF);        

    // Flag to indicate if an INDICATION needs to be sent to higher layers
    uint32_t *indication_triggered = (uint32_t*)jbpf_map_lookup_elem(&indication_trigger_map, &zero_index);
    if (!indication_triggered) {
        return JBPF_CODELET_FAILURE;
    }

    // Temporary map to store an incoming request.  Used as stack is too small for a local variable.
    slice_mgmt_req *input_req_tmp = (slice_mgmt_req*)jbpf_map_lookup_elem(&input_request_tmp, &zero_index);
    if (!input_req_tmp) {
        return JBPF_CODELET_FAILURE;
    }

    // Map to store "SET" requests.  This is maintained as the request might be for a specific sfn/sn
    slice_mgmt_set_request_t *set_request = (slice_mgmt_set_request_t*)jbpf_map_lookup_elem(&set_request_map, &zero_index);
    if (!set_request) {
        return JBPF_CODELET_FAILURE;
    }


    // has there has previously been a trigger to send the latest slice-config
    if (*indication_triggered == 1) {

        // send latest received config from the RAN

        slice_mgmt_ind* ind = (slice_mgmt_ind*)jbpf_get_output_buf(&slice_indication_map);
        if (!ind) {
            return JBPF_CODELET_FAILURE;
        }

        ind->timestamp = jbpf_time_get_ns();
        ind->sfn = sfn;
        ind->slot_index = slot_index;

        // map from jbpf_slice_allocation to slice_mgmt
        ind->slice_count = 0;
        for (i=0; i<data.num_slices; i++) {
            if (i >= JBPF_MAX_SLICES) return JBPF_CODELET_FAILURE;
            ind->slice[ind->slice_count % 16].pci = data.slices[i % JBPF_MAX_SLICES].pci;
            ind->slice[ind->slice_count % 16].plmn_id = data.slices[i % JBPF_MAX_SLICES].plmn_id;
            ind->slice[ind->slice_count % 16].nssai.sst = data.slices[i % JBPF_MAX_SLICES].nssai.sst;
            ind->slice[ind->slice_count % 16].nssai.sd = data.slices[i % JBPF_MAX_SLICES].nssai.sd;
            ind->slice[ind->slice_count % 16].min_prb_policy_ratio = data.slices[i % JBPF_MAX_SLICES].min_prb_policy_ratio;
            ind->slice[ind->slice_count % 16].max_prb_policy_ratio = data.slices[i % JBPF_MAX_SLICES].max_prb_policy_ratio;
            ind->slice[ind->slice_count % 16].priority = data.slices[i % JBPF_MAX_SLICES].priority;
            ind->slice_count++;
        }

        // send to the higher layer app
        if (jbpf_send_output(&slice_indication_map) < 0) {
            return JBPF_CODELET_FAILURE;
        }        

        jbpf_printf_debug("latest config sent to higher layers, ind->slice_count = %d\n", ind->slice_count);

        // clear trigger flag
        *indication_triggered = 0;
    }

    // get request from "slice_request_map"
    if (jbpf_control_input_receive(&slice_request_map, input_req_tmp, sizeof(slice_mgmt_req)) > 0) {

        if (input_req_tmp->msg_type == slice_mgmt_msg_type_GET_SLICE_ALLOC) {

            jbpf_printf_debug("GET_SLICE_ALLOC received from higher layers.\n");

            // request received to send latest slice config to higher layer app

            // set flag to send cfg to higher layer app
            *indication_triggered = 1;

        } else if (input_req_tmp->msg_type == slice_mgmt_msg_type_SET_SLICE_ALLOC) {

            jbpf_printf_debug("SET_SLICE_ALLOC received from higher layers\n");

            // request received to set new slice config
            
            // check set_req is present
            if (!input_req_tmp->has_set_req) {
                // require set_req not present !!
                return JBPF_CODELET_FAILURE;
            }

            // update the latest waiting set request in "set_request_map"
            memcpy(&set_request->request, &input_req_tmp->set_req, sizeof(slice_mgmt_set_req));
            set_request->requested = true;

        } else {
            // Unexpected msg_type in request
            return JBPF_CODELET_FAILURE;
        }
    }

    if (set_request->requested) {

        // does the request have sfn/slot set, and match the currennt sfn/slot of the RAN
        bool update_ran_now = 
            (!set_request->request.has_sfn        || set_request->request.sfn == sfn) ||
            (!set_request->request.has_slot_index || set_request->request.slot_index == slot_index);

        // update the RAN now if sf/slot matches.
        if (update_ran_now) {

            jbpf_printf_debug("New allocation will be configured now (sfn/slot=%d/%d) \n", sfn, slot_index);

            // clear flag so we dont repeatedly process the request
            set_request->requested = 0;            

            // set flag to send cfg to higher layer app
            *indication_triggered = 1;

            // update "data" with the requested config

            // validate that the set-request has no new slices, 
            if (set_request->request.slice_count > data.num_slices) {
                // the rtequest has too many slices. so this request will be dropped
                return JBPF_CODELET_FAILURE;
            }
            // validate that no static parameters have changed
            for (i=0; i<set_request->request.slice_count; i++) {
                // find slice
                bool slice_found = false;
                for (j=0; j<data.num_slices && (!slice_found); j++) {
                    slice_found = ((data.slices[j % JBPF_MAX_SLICES].pci == set_request->request.slice[i].pci) &&
                                        (data.slices[j % JBPF_MAX_SLICES].plmn_id == set_request->request.slice[i].plmn_id) &&
                                        (data.slices[j % JBPF_MAX_SLICES].nssai.sst == set_request->request.slice[i].nssai.sst) &&
                                        (data.slices[j % JBPF_MAX_SLICES].nssai.sd == set_request->request.slice[i].nssai.sd));
                }
                if (!slice_found) {
                    // slice could not be found
                    return JBPF_CODELET_FAILURE;
                }
            }

            // if we reach here all slices in the request are validated
            // update the dynamic paramters to those from the set-request
            for (i=0; i<set_request->request.slice_count; i++) {
                for (j=0; j<data.num_slices; j++) {
                    bool slice_found = ((data.slices[j % JBPF_MAX_SLICES].pci == set_request->request.slice[i].pci) &&
                                        (data.slices[j % JBPF_MAX_SLICES].plmn_id == set_request->request.slice[i].plmn_id) &&
                                        (data.slices[j % JBPF_MAX_SLICES].nssai.sst == set_request->request.slice[i].nssai.sst) &&
                                        (data.slices[j % JBPF_MAX_SLICES].nssai.sd == set_request->request.slice[i].nssai.sd));
                    if (slice_found) {
                        data.slices[j % JBPF_MAX_SLICES].min_prb_policy_ratio = set_request->request.slice[i].min_prb_policy_ratio;
                        data.slices[j % JBPF_MAX_SLICES].max_prb_policy_ratio = set_request->request.slice[i].max_prb_policy_ratio;
                        data.slices[j % JBPF_MAX_SLICES].priority = set_request->request.slice[i].priority;
                    }
                }
            }            

            // return resukt to show that an update has taken place
            return JBPF_CTRL_CODELET_SUCCESS;            
        }
    }

    return JBPF_CODELET_SUCCESS;
}
