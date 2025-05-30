# UE Indexing Across Subsystems

This document outlines how UE (User Equipment) indexes are managed and tracked across various subsystems in a disaggregated RAN architecture, specifically the DU (Distributed Unit), CU-CP (Central Unit - Control Plane), and CU-UP (Central Unit - User Plane).

## Overview

All UE-specific operations use a **UE index** as an identifier. However, each subsystem maintains its own UE index space, meaning the same UE may have different index values in the DU, CU-CP, and CU-UP.

To clarify this across the codebase, the following naming conventions are used for UE indices:

- `du_ue_index`
- `cu_cp_ue_index`
- `cu_up_ue_index`

## Subsystem UE Index Management

### DU (Distributed Unit)

When a UE is created at the DU, the following function is invoked:

#### Function: `du_ue_ctx_creation`

**Parameters:**

- `du_ue_index`
- `plmn` (Public Land Mobile Network)
- `nci` (NR Cell Identity)
- `pci` (Physical Cell ID)
- `tac` (Tracking Area Code)
- `crnti` (Cell Radio Network Temporary Identifier)

---

### CU-CP (Central Unit - Control Plane)

When a UE is created at the CU-CP, the following function is used:

#### Function: `cucp_uemgr_ue_add`

**Parameters:**

- `cu_cp_ue_index`
- `plmn`
- `pci`
- `rnti` (Radio Network Temporary Identifier)

**Mapping Note:**
The `cu_cp_ue_index` can be mapped to a `du_ue_index` using the tuple (`plmn`, `pci`, `rnti`).

---

### CU-UP (Central Unit - User Plane)

UE context setup in the CU-UP occurs via the **E1AP Bearer Setup** procedure. The following hooks are involved:

#### 1. `e1_cucp_bearer_context_setup`

**Parameters:**

- `cu_cp_ue_index`
- `gnb_cu_cp_ue_e1ap_id`

#### 2. `e1_cuup_bearer_context_setup`

**Parameters:**

- `cu_cp_ue_index`
- `gnb_cu_cp_ue_e1ap_id`
- `gnb_cu_up_ue_e1ap_id`

**Mapping Notes:**

- `gnb_cu_cp_ue_e1ap_id` corresponds to `cu_cp_ue_index`
- The tuple (`gnb_cu_cp_ue_e1ap_id`, `gnb_cu_up_ue_e1ap_id`) together identify the `cu_up_ue_index`

---

## PDCP Context (Packet Data Convergence Protocol)

PDCP hooks are invoked in both CU-CP (for SRBs) and CU-UP (for DRBs). A shared context structure is used:

```c
struct jbpf_pdcp_ctx_info {
    uint16_t ctx_id;       // Context ID (implementation-specific)
    uint32_t cu_ue_index;  // SRB: cu_cp_ue_index, DRB: cu_up_ue_index
    uint8_t  is_srb;       // true = SRB, false = DRB
    uint8_t  rb_id;        // SRB: 0=srb0, 1=srb1, 2=srb2
                           // DRB: 1=drb1, 2=drb2, 3=drb3, etc.
    uint8_t  rlc_mode;     // 0 = UM, 1 = AM
};


In CU-CP, PDCP hooks handle SRBs. Therefore, cu_ue_index refers to cu_cp_ue_index.

In CU-UP, PDCP hooks handle DRBs. Therefore, cu_ue_index refers to cu_up_ue_index.

# Example hook flow ...

```sh
hook_du_ue_ctx_creation: du_ue_index 0 tac 1 nrcgi=[ plmn=61712 nci=6733824 ] pci 1 tc_rnti 17922
hook_cucp_uemgr_ue_add: cu_cp_ue_index 1 plmn 00101 pci=1 rnti=17922
hook_pdcp_dl_creation: cu_ue_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_ue_index represents cu_cp_ue_index
hook_pdcp_ul_creation: cu_ue_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_ue_index represents cu_cp_ue_index
hook_e1_cucp_bearer_context_setup, cu_cp_ue_index=1 gnb_cu_cp_ue_e1ap_id=1
hook_pdcp_dl_creation: cu_ue_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_ue_index represents cu_up_ue_index
hook_pdcp_ul_creation: cu_ue_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_ue_index represents cu_up_ue_index
hook_e1_cuup_bearer_context_setup success, cu_up_ue_index 0  gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
hook_e1_cucp_bearer_context_modification, cu_cp_ue_index=1 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
hook_e1_cuup_bearer_context_modification success cu_up_ue_index=0 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
hook_pdcp_dl_creation: cu_ue_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_ue_index represents cu_cp_ue_index
hook_pdcp_ul_creation: cu_ue_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_ue_index represents cu_cp_ue_index
hook_e1_cucp_bearer_context_release, cu_cp_ue_index=1 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
hook_pdcp_ul_deletion: cu_ue_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_ue_index represents cu_up_ue_index
hook_pdcp_dl_deletion: cu_ue_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_ue_index represents cu_up_ue_index
hook_e1_cuup_bearer_context_release success cu_up_ue_index=0 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
hook_du_ue_ctx_deletion: du_ue_index 0
hook_pdcp_ul_deletion: cu_ue_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_ue_index represents cu_cp_ue_index
hook_pdcp_dl_deletion: cu_ue_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_ue_index represents cu_cp_ue_index
hook_pdcp_ul_deletion: cu_ue_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_ue_index represents cu_cp_ue_index
hook_pdcp_dl_deletion: cu_ue_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_ue_index represents cu_cp_ue_index
hook_cucp_uemgr_ue_remove: cu_cp_ue_index 1
```
