// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef MISC_UTILS_H
#define MISC_UTILS_H

#define JBPF_CTRL_CODELET_SUCCESS (1)
#define JBPF_CODELET_SUCCESS (0)
#define JBPF_CODELET_FAILURE (-1)


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
#endif // MISC_UTILS_H

