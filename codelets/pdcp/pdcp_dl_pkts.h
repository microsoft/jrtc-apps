// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef JRTC_APP_PDCP_SDUS
#define JRTC_APP_PDCP_SDUS


#define PDCP_REPORT_DL
#define PDCP_REPORT_UL
#define PDCP_REPORT_DL_DELAY_QUEUE


#define MAX_NUM_UE_RB (256)
//#define MAX_SDU_IN_FLIGHT (256 * 32 * 4)
#define MAX_SDU_IN_FLIGHT (256 * 32 * 1)
#define MAX_SDU_QUEUES (256)


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