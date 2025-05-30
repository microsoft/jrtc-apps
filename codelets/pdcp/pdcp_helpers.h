// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef JRTC_APP_PDCP_HELPERS
#define JRTC_APP_PDCP_HELPERS

// This file contains helper macros and functions for PDCP codelets.

// Macto to create an explicirt rbid...
// if srb, use rb_id as is, else add 10 to the rb_id.
// so srb=true rb_id-1, will reults in 1
// and srb=false rb_id-1, will result in 11.
#define RBID_2_EXPLICIT(is_srb, rb_id) ((is_srb) ? (rb_id) : ((rb_id) + 10))

#define RBID_FROM_EXPLICIT(explicit_rb_id, is_srb, rb_id) { \
    if (explicit_rb_id < 10) { \
        is_srb = true; \
        rb_id = explicit_rb_id; \
    } else { \
        is_srb = false; \
        rb_id = explicit_rb_id - 10; \
    } \
}

#endif


