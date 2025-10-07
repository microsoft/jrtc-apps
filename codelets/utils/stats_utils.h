// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef JRTC_STATS_UTILS_H
#define JRTC_STATS_UTILS_H

#include "jbpf_srsran_contexts.h"

#define MAX_NUM_UE (32)


#define STATS_INIT(__dest)       \
    do {                             \
        __dest.count = 0;            \
        __dest.total = 0;            \
        __dest.min = UINT32_MAX;     \
        __dest.max = 0;              \
    } while (0)


#define STATS_UPDATE(__dest, __src)  \
    do {                                 \
        __dest.count++;                  \
        if (__src < __dest.min) {        \
             __dest.min = __src;         \
        }                                \
        if (__src > __dest.max) {        \
            __dest.max = __src;          \
        }                                \
        __dest.total += __src;           \
    } while (0)


#define TRAFFIC_STATS_INIT(__dest)   \
    do {                                 \
        __dest.count = 0;                \
        __dest.total = 0;                \
    } while (0)


#define TRAFFIC_STATS_UPDATE(__dest, __v)   \
    do {                                        \
        __dest.count++;                         \
        __dest.total += __v;                    \
    } while (0)


#endif // JRTC_STATS_UTILS_H
