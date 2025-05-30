// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef JRTC_APP_PDCP_SDUS
#define JRTC_APP_PDCP_SDUS


#define PDCP_REPORT_DL
#define PDCP_REPORT_UL
#define PDCP_REPORT_DL_DELAY_QUEUE

// If you comment out PDCP_REPORT_DL_DELAY_QUEUE, 
// also comment out various linked maps 
// because they will be optimized out by the compiler
// # linked_maps:
// #   - map_name: sdu_events
// #     linked_codelet_name: pdcp_dl_new_sdu
// #     linked_map_name: sdu_events
// #   - map_name: sdu_queues
// #     linked_codelet_name: pdcp_dl_new_sdu
// #     linked_map_name: sdu_queues
// #   - map_name: delay_hash
// #     linked_codelet_name: pdcp_dl_new_sdu
// #     linked_map_name: delay_hash
// #   - map_name: queue_hash
// #     linked_codelet_name: pdcp_dl_new_sdu
// #     linked_map_name: queue_hash

// # - codelet_name: e1_cuup_bearer_context_setup
// #   codelet_path: ${JBPF_CODELETS}/pdcp/e1_cuup_bearer_context_setup.o
// #   hook_name: e1_cuup_bearer_context_setup
// #   priority: 1
// #   linked_maps:
// #     - map_name: last_notif_acked_map
// #       linked_codelet_name: pdcp_dl_delivery
// #       linked_map_name: last_notif_acked_map
// #     - map_name: last_notif_acked_hash
// #       linked_codelet_name: pdcp_dl_delivery
// #       linked_map_name: last_notif_acked_hash



#define MAX_NUM_UE_RB (256)
//#define MAX_SDU_IN_FLIGHT (256 * 32 * 4)
#define MAX_SDU_IN_FLIGHT (256 * 32 * 1)
#define MAX_SDU_QUEUES (256)
#define FIVE_SECOND_NS (5000000000)

typedef struct {
    uint64_t sdu_arrival_ns;
    uint64_t pdcpTx_ns;
    uint64_t rlcTxStarted_ns;
    uint64_t rlcDelivered_ns;
    uint32_t sdu_length;
} t_sdu_evs;

typedef struct {
    t_sdu_evs map[MAX_SDU_IN_FLIGHT];
    uint32_t map_count;
} t_sdu_events;


typedef struct {
    uint32_t pkts;
    uint32_t bytes;
} t_queue;


typedef struct {
    t_queue map[MAX_SDU_QUEUES];
    uint32_t map_count;
} t_sdu_queues;

typedef struct {
    uint32_t ack[MAX_SDU_IN_FLIGHT];
    uint32_t ack_count;
} t_last_acked;


#endif