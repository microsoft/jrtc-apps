// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef JRTC_MAC_HELPERS_H
#define JRTC_MAC_HELPERS_H

#include "jbpf_srsran_contexts.h"

#include "../utils/stats_utils.h"

#define MAX_NUM_UE (32)


#define MAC_HARQ_STATS_INIT(__dest, __cell_id, __rnti, __du_ue_index)  \
    do {                                                                          \
        __dest.cell_id = __cell_id;                                               \
        __dest.rnti = __rnti;                                                     \
        __dest.du_ue_index = __du_ue_index;                                       \
        STATS_INIT(__dest.cons_retx);                                         \
        STATS_INIT(__dest.mcs);                                               \
        __dest.perHarqTypeStats[JBPF_HARQ_EVENT_TX].count = 0;                          \
        __dest.perHarqTypeStats[JBPF_HARQ_EVENT_TX].has_cqi = false;                    \
        TRAFFIC_STATS_INIT(__dest.perHarqTypeStats[JBPF_HARQ_EVENT_TX].tbs_bytes);  \
        __dest.perHarqTypeStats[JBPF_HARQ_EVENT_RETX].count = 0;                        \
        __dest.perHarqTypeStats[JBPF_HARQ_EVENT_RETX].has_cqi = false;                  \
        TRAFFIC_STATS_INIT(__dest.perHarqTypeStats[JBPF_HARQ_EVENT_RETX].tbs_bytes);\
        __dest.perHarqTypeStats[JBPF_HARQ_EVENT_FAILURE].count = 0;                     \
        __dest.perHarqTypeStats[JBPF_HARQ_EVENT_FAILURE].has_cqi = false;               \
        TRAFFIC_STATS_INIT(__dest.perHarqTypeStats[JBPF_HARQ_EVENT_FAILURE].tbs_bytes); \
    } while (0) 

#define MAC_HARQ_STATS_INIT_UL MAC_HARQ_STATS_INIT_DL

#define MAC_HARQ_STATS_INIT_DL(__dest, __cell_id, __rnti, __du_ue_index)          \
    do {                                                                        \
        MAC_HARQ_STATS_INIT(__dest, __cell_id, __rnti, __du_ue_index);            \
        __dest.perHarqTypeStats[JBPF_HARQ_EVENT_TX].has_cqi = true;                     \
        STATS_INIT(__dest.perHarqTypeStats[JBPF_HARQ_EVENT_TX].cqi);                    \
        __dest.perHarqTypeStats[JBPF_HARQ_EVENT_RETX].has_cqi = true;                   \
        STATS_INIT(__dest.perHarqTypeStats[JBPF_HARQ_EVENT_RETX].cqi);                  \
        __dest.perHarqTypeStats[JBPF_HARQ_EVENT_FAILURE].has_cqi = true;                \
        STATS_INIT(__dest.perHarqTypeStats[JBPF_HARQ_EVENT_FAILURE].cqi);               \
    } while (0) 



#endif // JRTC_MAC_HELPERS_H
