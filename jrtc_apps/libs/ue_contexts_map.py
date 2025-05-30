# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
#
# This codelet simply forwards the message.
#
#
# UE Indexing Across Subsystems
#
# This comment outlines how UE (User Equipment) indexes are managed and tracked across 
# various subsystems (DU, CU-CP, and CU-UP).
#
# All functions invoked as hooks for UE-specific operations will include a "UE index".
# However, the DU, CU-CP, and CU-UP subsystems manage their UE indexes independently.
# As a result, the same UE may have different index values in each subsystem.
#
# To clarify this in the code, the context structures use the following field names:
#     - du_index
#     - cu_cp_index
#     - cu_up_index
#
# Mapping UE indexes across subsystems involves the following conventions:
#
# DU (Distributed Unit):
# -----------------------
# The function `du_ue_ctx_creation` is called when a UE is created at the DU.
# Parameters:
#     - du_index
#     - plmn
#     - nci
#     - pci
#     - tac
#     - crnti
#
# CU-CP (Central Unit - Control Plane):
# -------------------------------------
# The function `cucp_uemgr_ue_add` is called when a UE is created at the CU-CP.
# Parameters:
#     - cu_cp_index
#     - plmn
#     - pci
#     - rnti
#
# The `cu_cp_index` can be mapped to a `du_index` based on matching (plmn, pci, rnti).
#
# CU-UP (Central Unit - User Plane):
# ----------------------------------
# The UE context in the CU-UP is set up via the E1AP Bearer Setup procedure.
# The following hooks are invoked:
#
#     - `e1_cucp_bearer_context_setup`
#         Parameters: cu_cp_index, gnb_cu_cp_ue_e1ap_id
#
#     - `e1_cuup_bearer_context_setup`
#         Parameters: cu_cp_index, gnb_cu_cp_ue_e1ap_id, gnb_cu_up_ue_e1ap_id
#
# Mapping details:
#     - `gnb_cu_cp_ue_e1ap_id` corresponds to `cu_cp_index`
#     - (`gnb_cu_cp_ue_e1ap_id`, `gnb_cu_up_ue_e1ap_id`) together identify the `cu_up_index`
#
# PDCP (Packet Data Convergence Protocol):
# ----------------------------------------
# PDCP hooks are invoked in both CU-CP (for SRBs) and CU-UP (for DRBs), and share a unified 
# context structure:
#
#     struct jbpf_pdcp_ctx_info {
#         uint16_t ctx_id;       # Context ID (implementation specific)
#         uint32_t cu_index;  # SRB: cu_cp_index, DRB: cu_up_index
#         uint8_t  is_srb;       # true = SRB, false = DRB
#         uint8_t  rb_id;        # SRB: 0=srb0, 1=srb1, 2=srb2
#                                # DRB: 1=drb1, 2=drb2, 3=drb3, etc.
#         uint8_t  rlc_mode;     # 0 = UM, 1 = AM
#     }
#
# Notes:
#     - In CU-CP, hooks are called for SRBs. Thus, `cu_index` refers to `cu_cp_index`.
#     - In CU-UP, hooks are called for DRBs. Thus, `cu_index` refers to `cu_up_index`.
#
# Example hook flow ...
#
#   hook_du_ue_ctx_creation: du_index 0 tac 1 nrcgi=[ plmn=61712 nci=6733824 ] pci 1 tc_rnti 17922
#   hook_cucp_uemgr_ue_add: cu_cp_index 1 plmn 00101 pci=1 rnti=17922
#   hook_pdcp_dl_creation: cu_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_pdcp_ul_creation: cu_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_e1_cucp_bearer_context_setup, cu_cp_index=1 gnb_cu_cp_ue_e1ap_id=1
#   hook_pdcp_dl_creation: cu_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_index represents cu_up_index
#   hook_pdcp_ul_creation: cu_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_index represents cu_up_index
#   hook_e1_cuup_bearer_context_setup success, cu_up_index 0  gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
#   hook_e1_cucp_bearer_context_modification, cu_cp_index=1 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
#   hook_e1_cuup_bearer_context_modification success cu_up_index=0 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
#   hook_pdcp_dl_creation: cu_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_pdcp_ul_creation: cu_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_e1_cucp_bearer_context_release, cu_cp_index=1 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
#   hook_pdcp_ul_deletion: cu_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_index represents cu_up_index
#   hook_pdcp_dl_deletion: cu_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_index represents cu_up_index
#   hook_e1_cuup_bearer_context_release success cu_up_index=0 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
#   hook_du_ue_ctx_deletion: du_index 0
#   hook_pdcp_ul_deletion: cu_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_pdcp_dl_deletion: cu_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_pdcp_ul_deletion: cu_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_pdcp_dl_deletion: cu_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_cucp_uemgr_ue_remove: cu_cp_index 1
#


import sys
from dataclasses import dataclass, asdict
from typing import List, Tuple



##########################################
@dataclass(frozen=True)
class unique_index:
    src: str
    idx: int

    def __str__(self):
        return f'{{"src":"{self.src}", "idx":{self.idx}}}'

##########################################
@dataclass
class ue_context:
    du_index: unique_index
    cucp_index: unique_index
    cuup_index: unique_index
    plmn: int
    nci: int
    pci: int
    tac: int
    crnti: int
    e1_bearers: List[Tuple[int, int]]     # tuple of (cucp_ue_e1ap_id, cuup_ue_e1ap_id)
    tmsi: int = None  
    
    def __init__(self, plmn: int, pci: int, crnti: int, du_index: unique_index = None, cucp_index: unique_index = None, cuup_index: unique_index = None,
                 nci: int=None, tac: int=None):
        self.plmn = plmn
        self.pci = pci
        self.crnti = crnti
        # optional
        self.nci = nci
        self.tac = tac
        self.du_index = du_index
        self.cucp_index = cucp_index
        self.cuup_index = cuup_index
        self.e1_bearers = []

    def used(self) -> bool:
        """
        Check if the UE context is used.
        :return: True if the context is used, False otherwise.
        """
        if self.du_index is not None:
            return True
        if self.cucp_index is not None:
            return True
        if (self.cuup_index is not None) and (len(self.e1_bearers) > 0):
            return True
        return False

    def get_bearer(self, cucp_ue_e1ap_id: unique_index) -> Tuple[Tuple[str, int], Tuple[str, int]]:
        for bearer in self.e1_bearers:
            if bearer[0] == cucp_ue_e1ap_id:
                return bearer
        return None, None
        
    def get_bearer_NoSrcCheck(self, cucp_ue_e1ap_id: int) -> Tuple[Tuple[str, int], Tuple[str, int]]:
        for bearer in self.e1_bearers:
            if bearer[0][1] == cucp_ue_e1ap_id:
                return bearer
        return None, None

    def __str__(self):
        return (f"UEContext(du_index={self.du_index}, "
                f"cucp_index={self.cucp_index}, cuup_index={self.cuup_index}, "
                f"plmn={self.plmn}, nci={self.nci}, pci={self.pci}, "
                f"tac={self.tac}, crnti={self.crnti}, tmsi={self.tmsi}, "
                f"e1_bearers={self.e1_bearers})")

    def to_dict(self):
        return {
            "du_index": self.du_index,
            "cucp_index": self.cucp_index,
            "cuup_index": self.cuup_index,
            "plmn": self.plmn,
            "nci": self.nci,
            "pci": self.pci,
            "tac": self.tac,
            "crnti": self.crnti,
            "tmsi": self.tmsi,
            "e1_bearers": self.e1_bearers
        }


###########################################################################################################
class ue_contexts_map:
    """
    This class is used to manage UE contexts in the srsRAN system.
    It provides methods to create, delete, and modify UE contexts.
    """

    ####################################################################
    def __init__(self, dbg: bool=False):
        self.dbg = dbg
        self.context_id = 0       # will just increase by 1 for each new context.  No need to handle wrap as we'll never reach that
        self.contexts = {}
        self.contexts_by_du_index = {}
        self.contexts_by_cucp_index = {}
        self.contexts_by_cuup_index = {}
        self.contexts_by_cucp_ue_e1ap_id = {}
        self.contexts_by_cuup_ue_e1ap_id = {}

    ####################################################################
    def context_create(self, plmn: int, pci: int, crnti: int, du_index: unique_index = None, cucp_index: unique_index = None, cuup_index: unique_index = None,
        nci: int=None, tac: int=None) -> None:
        if self.dbg:
            print(f"context_create: plmn={plmn} pci={pci} crnti={crnti} du_index={du_index} cucp_index={cucp_index} cuup_index={cuup_index} nci={nci} tac={tac}")
        ue = ue_context(plmn, pci, crnti, du_index=du_index, cucp_index=cucp_index, cuup_index=cuup_index, nci=nci, tac=tac)
        # add mappings
        self.contexts[self.context_id] = ue
        if ue.du_index is not None:
            self.set_du_index(self.context_id, du_index)
        if ue.cucp_index is not None:
            self.set_cucp_index(self.context_id, cucp_index)
        if ue.cuup_index is not None:
            self.set_cuup_index(self.context_id, cuup_index)
        # increment context id for next context
        self.context_id += 1

    ####################################################################
    def context_delete(self, ue_id: int) -> None:
        if ue_id in self.contexts:
            if self.dbg:
                print(f"context_delete: ue_id={ue_id}")
            ue = self.contexts[ue_id]
            # Also remove from the other mappings
            self.contexts_by_du_index.pop(ue.du_index, None)
            self.contexts_by_cucp_index.pop(ue.cucp_index, None)
            self.contexts_by_cuup_index.pop(ue.cuup_index, None)
            for b in ue.e1_bearers:
                self.contexts_by_cucp_ue_e1ap_id.pop(b[0], None)
                self.contexts_by_cuup_ue_e1ap_id.pop(b[1], None)
            # remove context
            self.contexts.pop(ue_id, None)

    ####################################################################
    def delete_unused_context(self, ue_id: int) -> None:
        if ue_id in self.contexts:
            if self.contexts[ue_id].used():
                return
            if self.dbg:
                print(f"delete_unused_context: ue_id={ue_id}")
            self.contexts.pop(ue_id, None)

    ####################################################################
    def set_du_index(self, ue_id: int, du_index: unique_index) -> None:
        if ue_id not in self.contexts:
            if self.dbg:
                print(f"UE context with ID {ue_id} does not exist.")
            return
        if self.dbg:
            print(f"set_du_index: ue_id={ue_id} du_index={du_index}")
        self.contexts[ue_id].du_index = du_index
        self.contexts_by_du_index[du_index] = ue_id

    ####################################################################
    def clear_du_index(self, ue_id: int) -> None:
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        if self.dbg:
            print(f"clear_du_index: ue_id={ue_id}")
        du_index = self.contexts[ue_id].du_index
        self.contexts[ue_id].du_index = None
        self.contexts_by_du_index.pop(du_index, None)
        self.delete_unused_context(ue_id)

    ####################################################################
    def set_cucp_index(self, ue_id: int, cucp_index: unique_index) -> None:
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        if self.dbg:
            print(f"set_cucp_index: ue_id={ue_id} cucp_index={cucp_index}")
        self.contexts[ue_id].cucp_index = cucp_index
        self.contexts_by_cucp_index[cucp_index] = ue_id

    ####################################################################
    def clear_cucp_index(self, ue_id: int) -> None:
        if ue_id not in self.contexts:
            if self.dbg:
                print(f"UE context with ID {ue_id} does not exist.")
            return
        if self.dbg:
            print(f"clear_cucp_index: ue_id={ue_id}")
        cucp_index = self.contexts[ue_id].cucp_index
        self.contexts[ue_id].cucp_index = None
        self.contexts_by_cucp_index.pop(cucp_index, None)
        self.delete_unused_context(ue_id)

    ####################################################################
    def set_cuup_index(self, ue_id: int, cuup_index: unique_index) -> None:
        if ue_id not in self.contexts:
            if self.dbg:
                print(f"UE context with ID {ue_id} does not exist.")
            return
        if self.dbg:
            print(f"set_cuup_index: ue_id={ue_id} cuup_index={cuup_index}")
        self.contexts[ue_id].cuup_index = cuup_index
        self.contexts_by_cuup_index[cuup_index] = ue_id

    ####################################################################
    def clear_cuup_index(self, ue_id: int) -> None:
        if ue_id not in self.contexts:
            if self.dbg:
                print(f"UE context with ID {ue_id} does not exist.")
            return
        if self.dbg:
            print(f"clear_cuup_index: ue_id={ue_id}")        
        cuup_index = self.contexts[ue_id].cuup_index
        self.contexts[ue_id].cuup_index = None
        self.contexts_by_cuup_index.pop(cuup_index, None)
        self.delete_unused_context(ue_id)

    ####################################################################
    def set_cucp_ue_e1ap_id(self, ue_id: int, cucp_ue_e1ap_id: unique_index) -> None:
        if ue_id not in self.contexts:
            if self.dbg:
                print(f"UE context with ID {ue_id} does not exist.")
            return
        if self.dbg:
            print(f"set_cucp_ue_e1ap_id: ue_id={ue_id} cucp_ue_e1ap_id={cucp_ue_e1ap_id}")
        bearer = (cucp_ue_e1ap_id, None)
        self.contexts[ue_id].e1_bearers.append(bearer)
        self.contexts_by_cucp_ue_e1ap_id[cucp_ue_e1ap_id] = ue_id

    ####################################################################
    def clear_cucp_ue_e1ap_id(self, ue_id: int, cucp_ue_e1ap_id: unique_index) -> None:
        if ue_id not in self.contexts:
            if self.dbg:
                print(f"UE context with ID {ue_id} does not exist.")
            return

        if self.dbg: 
            print(f"clear_cucp_ue_e1ap_id: ue_id={ue_id} cucp_ue_e1ap_id={cucp_ue_e1ap_id}")

        # remove the bearer with the matching cucp_ue_e1ap_id
        bearer = None
        for i, b in enumerate(self.contexts[ue_id].e1_bearers):
            if b[0] == cucp_ue_e1ap_id:
                bearer = self.contexts[ue_id].e1_bearers.pop(i)
                
        if bearer is not None:
            self.contexts_by_cucp_ue_e1ap_id.pop(bearer[0], None)
            self.contexts_by_cuup_ue_e1ap_id.pop(bearer[1], None)
            # if no more bearers are present, remove the cuup_index too
            if len(self.contexts[ue_id].e1_bearers) == 0:
                self.clear_cuup_index(ue_id)
            self.delete_unused_context(ue_id)
        

    ####################################################################
    def set_cuup_ue_e1ap_id(self, ue_id: int, cucp_ue_e1ap_id: unique_index, cuup_ue_e1ap_id: unique_index) -> None:
        if ue_id not in self.contexts:
            if self.dbg:
                print(f"UE context with ID {ue_id} does not exist.")
            return

        if self.dbg:
            print(f"set_cuup_ue_e1ap_id: ue_id={ue_id} cucp_ue_e1ap_id={cucp_ue_e1ap_id} cuup_ue_e1ap_id={cuup_ue_e1ap_id}")

        # update the bearer with the matching cucp_ue_e1ap_id with the cuup_ue_e1ap_id
        for i, b in enumerate(self.contexts[ue_id].e1_bearers):
            if b[0] == cucp_ue_e1ap_id:
                self.contexts[ue_id].e1_bearers[i] = (b[0], cuup_ue_e1ap_id)
                break
        else:
            if self.dbg:
                print(f"Bearer with cucp_ue_e1ap_id {cucp_ue_e1ap_id} not found in UE context {ue_id}.")
            return
        self.contexts_by_cuup_ue_e1ap_id[cuup_ue_e1ap_id] = ue_id

    ####################################################################
    def clear_cuup_ue_e1ap_id(self, ue_id: int, cuup_ue_e1ap_id: unique_index) -> None:
        if ue_id not in self.contexts:
            if self.dbg:
                print(f"UE context with ID {ue_id} does not exist.")
            return

        if self.dbg:
            print(f"clear_cuup_ue_e1ap_id: ue_id={ue_id} cuup_ue_e1ap_id={cuup_ue_e1ap_id}")
        
        # remove the bearer with the matching cuup_ue_e1ap_id
        bearer = None
        for i, b in enumerate(self.contexts[ue_id].e1_bearers):
            if b[1] == cuup_ue_e1ap_id:
                bearer = self.contexts[ue_id].e1_bearers.pop(i)

        if bearer is not None:
            self.contexts_by_cucp_ue_e1ap_id.pop(bearer[0], None)
            self.contexts_by_cuup_ue_e1ap_id.pop(bearer[1], None)
            # if no more bearers are present, remove the cuup_index too
            if len(self.contexts[ue_id].e1_bearers) == 0:
                self.clear_cuup_index(ue_id)
            self.delete_unused_context(ue_id)        

    ####################################################################
    def getid_by_du_cucp_unique_info(self, plmn: int, pci:int, rnti: int) -> int:
        filtered_contexts = {
            k: v for k, v in self.contexts.items()
            if v.plmn == plmn and v.pci == pci and v.crnti == rnti
        }
        if len(filtered_contexts) == 1:
            return list(filtered_contexts.keys())[0]
        elif len(filtered_contexts) > 1:
            raise ValueError("Multiple UE contexts found for the given PLMN, PCI, and RNTI.")

        # if we reach here, it means no context was found
        return None 
        
    #####################################################################
    # This is as above, except it search based on the PCI and RNTI only.
    # This is used for the FAPI case where the PLMN is not available
    # --------------- TBD:
    # Currently the FAPI is not prividing the "pci" either, so for now just use the rnti.
    # This means it will only woek for one DU.
    # 
    def getid_by_pci_rnti(self, pci: int, rnti: int) -> int:

        filtered_contexts = {
            k: v for k, v in self.contexts.items()
            if v.crnti == rnti
            # TBD : add pci too
        }
        if len(filtered_contexts) == 1:
            return list(filtered_contexts.keys())[0]

        # if we reach here, it means no context or >=2 was found
        return None 

    #####################################################################
    def getue_by_id(self, ue_id: int) -> int:
        return self.contexts.get(ue_id, None)
    
    #####################################################################
    def getuectx(self, ue_id: int) -> ue_context:
        if ue_id is None:
            return None
        if ue_id not in self.contexts:
            if self.dbg:
                print(f"getuectx: UE context with ID {ue_id} does not exist.")
            return None
        return self.contexts[ue_id]

    #####################################################################
    def getid_by_du_index(self, du_src: str, du_index: int) -> int:
        du_index = unique_index(du_src, du_index)
        return self.contexts_by_du_index.get(du_index, None)

    #####################################################################
    def getid_by_cucp_index(self, cucp_src: str, cucp_index: int) -> int:
        cucp_index = unique_index(cucp_src, cucp_index)
        return self.contexts_by_cucp_index.get(cucp_index, None)

    #####################################################################
    def getid_by_cuup_index(self, cuup_src: str, cuup_index: int) -> int:
        cuup_index = unique_index(cuup_src, cuup_index)
        return self.contexts_by_cuup_index.get(cuup_index, None)

    #####################################################################
    def getid_by_cucp_ue_e1ap_id(self, cucp_src: str, cucp_ue_e1ap_id: int) -> int:
        cucp_ue_e1ap_id = (cucp_src, cucp_ue_e1ap_id)
        return self.contexts_by_cucp_ue_e1ap_id.get(cucp_ue_e1ap_id, None)

    #####################################################################
    def getid_by_cucp_ue_e1ap_id_NoSrcCheck(self, cucp_ue_e1ap_id: int) -> int:
        # find using only the 2nd element of the tuple
        # as the src is not available
        filtered_contexts = {
            k: v for k, v in self.contexts_by_cucp_ue_e1ap_id.items()
            if k[1] == cucp_ue_e1ap_id
        }
        if len(filtered_contexts) > 0:
            return list(filtered_contexts.values())[0]
        return None
        
    #####################################################################
    def getid_by_cuup_ue_e1ap_id(self, cucu_src: str, cuup_ue_e1ap_id: int) -> int:
        cuup_ue_e1ap_id = (cucu_src, cuup_ue_e1ap_id)
        return self.contexts_by_cuup_ue_e1ap_id.get(cuup_ue_e1ap_id, None)

    ####################################################################
    def get_e1_bearer_NoSrcCheck(self, cucp_ue_e1ap_id: int) -> (int, Tuple[Tuple[str, int], Tuple[str, int]]):
        ue_id = self.getid_by_cucp_ue_e1ap_id_NoSrcCheck(cucp_ue_e1ap_id)
        if ue_id is None:
            if self.dbg:
                print(f"get_e1_bearer_NoSrcCheck: UE context with cucp_ue_e1ap_id {cucp_ue_e1ap_id} not found.")
            return None, (None, None)
        v = ue_id, self.contexts[ue_id].get_bearer_NoSrcCheck(cucp_ue_e1ap_id)
        return ue_id, self.contexts[ue_id].get_bearer_NoSrcCheck(cucp_ue_e1ap_id)

    ####################################################################
    def hook_du_ue_ctx_creation(self, du_src: str, du_index: int, plmn: int, pci: int, crnti: int, tac: int, nci: int) -> None:
        """
        Create a UE context in the DU subsystem.

        :param du_index: The src/index of the UE in the DU subsystem.
        :param tac: Tracking Area Code.
        :param plmn: Public Land Mobile Network identifier.
        :param nci: NR Cell Identity.
        :param pci: Physical Cell Identity.
        :param crnti: C-RNTI (Cell Radio Network Temporary Identifier).
        """

        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_du_ue_ctx_creation: du_src={du_src} du_index={du_index} plmn={plmn} pci {pci} tc_rnti {crnti} tac {tac} nci={nci} ] ")
        
        # Check if the UE context with the du index already exists
        # It should not exist, do if it does, delete it
        ue_id = self.getid_by_du_index(du_src, du_index)
        if ue_id is not None:
            if self.dbg:
                print(f"Unexpected UE context with du_src {du_src} du_index {du_index} already exists.  Stale UE will be deleted")
            self.context_delete(ue_id)

        du_index = unique_index(du_src, du_index)

        # Check if the UE context with the unique info already exists
        # It should not exist, do if it does, delete it
        ue_id = self.getid_by_du_cucp_unique_info(plmn, pci, crnti)
        if ue_id is not None:
            if self.dbg:
                print(f"Unexpected UE context with [plmn={plmn} pci={pci} crnti={crnti}] already exists.  Stale UE will be deleted")
            self.context_delete(ue_id)

        # Create a new UE context
        self.context_create(plmn, pci, crnti, du_index=du_index, nci=nci, tac=tac)

    ####################################################################
    def hook_du_ue_ctx_update_crnti(self, du_src: str, du_index: int, crnti: int) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_du_ue_ctx_update_crnti: du_src {du_src} du_index {du_index} crnti {crnti}")

        ue_id = self.getid_by_du_index(du_src, du_index)
        if ue_id is None:
            if self.dbg:
                print(f"UE for du_src {du_src} du_index {du_index} could not be found.")
            return
        self.contexts[ue_id].crnti = crnti

    ####################################################################
    def hook_du_ue_ctx_deletion(self, du_src: str, du_index: int) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_du_ue_ctx_deletion: du_src {du_src} du_index {du_index}")
        ue_id = self.getid_by_du_index(du_src, du_index)
        if ue_id is not None:
            self.clear_du_index(ue_id)

    ####################################################################
    def hook_cucp_uemgr_ue_add(self, cucp_src: str, cucp_index: str, plmn: int, pci: int, crnti: int) -> None:
        """
        Create a UE context in the CU-CP subsystem.

        :param cu_cp_index: The index of the UE in the CU-CP subsystem.
        :param plmn: Public Land Mobile Network identifier.
        :param pci: Physical Cell Identity.
        :param crnti: C-RNTI (Cell Radio Network Temporary Identifier).
        """

        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_cucp_uemgr_ue_add: cucp_src={cucp_src} cucp_index {cucp_index} plmn {plmn} pci={pci} rnti={crnti}")

        # Check if a UE context with the cucp index already exists
        # It should not, so delete it if it does 
        ue_id = self.getid_by_cucp_index(cucp_src, cucp_index)
        if ue_id is not None:
            if self.dbg:
                print(f"Unexpected UE context with cucp_src {cucp_src} cucp_index {cucp_index} already exists.  Stale UE will be deleted")
            self.context_delete(ue_id)

        cucp_index = unique_index(cucp_src, cucp_index)

        # Check if a UE context with the unique info already exists
        # If it does not 
        #    create a new one
        # If it does, 
        #   check if the cucp index is currently set.
        #   If it is, delete the UE and create a new one
        #   If it is not, just update the cucp index
        ue_id = self.getid_by_du_cucp_unique_info(plmn, pci, crnti)
        if ue_id is None:
            # Create a new UE context
            self.context_create(plmn, pci, crnti, cucp_index=cucp_index)
        else:
            if self.contexts[ue_id].cucp_index is not None:
                if self.dbg:
                    print(f"Unexpected UE context with [plmn={plmn} pci={pci} crnti={crnti}] already exists.  Stale UE will be deleted")
                self.context_delete(ue_id)
                # Create a new UE context
                self.context_create(plmn, pci, crnti, cucp_index=cucp_index)
            else:
                if self.dbg:
                    print(f"UE context with [plmn={plmn} pci={pci} crnti={crnti}] already exists.  Setting cucp index")
                self.set_cucp_index(ue_id, cucp_index)
                if self.dbg:
                    print(f"UE context updated: {self.contexts[ue_id]}")

    ####################################################################
    def hook_cucp_uemgr_ue_remove(self, cucp_src: str, cucp_index: int) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_cucp_uemgr_ue_remove: cucp_src {cucp_src} cucp_index {cucp_index}")
        ue_id = self.getid_by_cucp_index(cucp_src, cucp_index)
        if ue_id is not None:
            self.clear_cucp_index(ue_id)

    ####################################################################
    def hook_e1_cucp_bearer_context_setup(self, cucp_src: str, cucp_index: int, gnb_cucp_ue_e1ap_id: int) -> None:
        """
        Handle the E1AP Bearer Context Setup for CU-CP.

        :param cucp_index: The index of the UE in the CU-CP subsystem.
        :param gnb_cu_cp_ue_e1ap_id: The E1AP ID for the CU-CP.
        """

        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_e1_cucp_bearer_context_setup, cucp_src={cucp_src} cucp_index={cucp_index} gnb_cucp_ue_e1ap_id={gnb_cucp_ue_e1ap_id}")

        gnb_cucp_ue_e1ap_id_tup = (cucp_src, gnb_cucp_ue_e1ap_id)

        # Check if a UE context with the gnb_cucp_ue_e1ap_id already exists
        # It should not, so clear it if it does 
        ue_id = self.getid_by_cucp_ue_e1ap_id(cucp_src, gnb_cucp_ue_e1ap_id)
        if ue_id is not None:
            if self.dbg:
                print(f"Unexpected UE context with cucp_src {cucp_src} gnb_ccup_ue_e1ap_id {gnb_cucp_ue_e1ap_id} already exists")
            self.clear_cucp_ue_e1ap_id(ue_id, gnb_cucp_ue_e1ap_id_tup)

        # Check if a UE context with the cucp index already exists
        # It should, so return if it does not
        ue_id = self.getid_by_cucp_index(cucp_src, cucp_index)    
        if ue_id is None:
            if self.dbg:
                print(f"UE context with cucp_src {cucp_src} cucp_index {cucp_index} not found. !!")
            return
    
        # update the gnb_cucp_ue_e1ap_id
        self.set_cucp_ue_e1ap_id(ue_id, gnb_cucp_ue_e1ap_id_tup)

    ####################################################################
    def hook_e1_cuup_bearer_context_setup(self, cuup_src: str, cuup_index: int, gnb_cucp_ue_e1ap_id: int, gnb_cuup_ue_e1ap_id: int, success: bool) -> None:
        """
        Handle the E1AP Bearer Context Setup for CU-UP.

        :param cuup_index: The index of the UE in the CU-UP subsystem.
        :param gnb_cu_cp_ue_e1ap_id: The E1AP ID for the CU-CP.
        :param gnb_cu_up_ue_e1ap_id: The E1AP ID for the CU-UP.
        """

        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_e1_cuup_bearer_context_setup success={success}, cuup_src={cuup_src} cuup_index={cuup_index}  gnb_cu_cp_ue_e1ap_id={gnb_cucp_ue_e1ap_id} gnb_cu_up_ue_e1ap_id={gnb_cuup_ue_e1ap_id}")

        cuup_index = unique_index(cuup_src, cuup_index)
        gnb_cuup_ue_e1ap_id_tup = (cuup_src, gnb_cuup_ue_e1ap_id)

        # Check if a UE context with the gnb_cuup_ue_e1ap_id already exists
        # It should not, so clear it if it does 
        ue_id = self.getid_by_cuup_ue_e1ap_id(cuup_src, gnb_cuup_ue_e1ap_id)
        if ue_id is not None:
            if self.dbg:
                print(f"Unexpected UE context with cuup_src {cuup_src} gnb_cuup_ue_e1ap_id {gnb_cuup_ue_e1ap_id} already exists")
            self.clear_cuup_ue_e1ap_id(ue_id, gnb_cuup_ue_e1ap_id_tup)

        # check that the e1 bearer has cuup_ue_e1ap_id=None.
        # If it is set, clear it
        ue_id, bearer = self.get_e1_bearer_NoSrcCheck(gnb_cucp_ue_e1ap_id)
        if ue_id is None:
            # the bearer does not exist, the mapping cannot be done
            return
        if bearer[1] is not None and bearer[1] != gnb_cuup_ue_e1ap_id_tup:
            # the bearer already has a cuup_ue_e1ap_id, clear it
            self.clear_cuup_ue_e1ap_id(ue_id, bearer[1])
            # the mapping cannot be done
            return

        # if this point it reached, it means we have the ue context with a matching bearer (cucp_ue_e1ap_id, None)

        # check if the cucp index is different

        ue_id2 = self.getid_by_cuup_index(cuup_src, cuup_index)
        if ue_id2 is not None and ue_id2 != ue_id:
            if self.dbg:
                print(f"Unexpected UE context with cuup_src {cuup_src} cuup_index {cuup_index} already exists.  Stale UE will be deleted")
            self.context_delete(ue_id2)
            return

        # if this is a failure, clear the cucp_ue_e1ap_id
        if success is False:
            # remove the cucp_ue_e1ap_id from the context
            s.clear_cucp_ue_e1ap_id(ue_id, bearer[0])
            return

        # set the cuup_ue_e1ap_id
        self.set_cuup_ue_e1ap_id(ue_id, bearer[0], gnb_cuup_ue_e1ap_id_tup)
        # update the cuup index
        self.set_cuup_index(ue_id, cuup_index)

    #####################################################################
    def hook_e1_cuup_bearer_context_release(self, cuup_src: str, cuup_index: int, cucp_ue_e1ap_id: int, cuup_ue_e1ap_id: int, success: bool) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_e1_cuup_bearer_context_release success {success} cuup_src {cuup_src} cuup_index {cuup_index} gnb_cucp_ue_e1ap_id={cucp_ue_e1ap_id} gnb_cuup_ue_e1ap_id={cuup_ue_e1ap_id}")

        cuup_index = unique_index(cuup_src, cuup_index)

        if success is False:
            return

        # Note here we just match on the cuup_ue_e1ap_id, and the cucp_ue_e1ap_id  value is not chcked.  ]
        # This is because we dont have the cucp_src.
        # Regardless, this is required in case the capture is started late, and we need to clean up stale UEs.
        
        ue_id = self.getid_by_cuup_ue_e1ap_id(cuup_src, cuup_ue_e1ap_id)
        if ue_id is not None:
            cuup_ue_e1ap_id_tup = (cuup_src, cuup_ue_e1ap_id)
            self.clear_cuup_ue_e1ap_id(ue_id, cuup_ue_e1ap_id_tup)

    ####################################################################
    def add_tmsi(self, cucp_src: str, cucp_index: int, tmsi: int) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"add_tmsi: cucp_src={cucp_src} cucp_index={cucp_index} tmsi={tmsi}")
        ue_id = self.getid_by_cucp_index(cucp_src, cucp_index)
        if ue_id is None:
            if self.dbg:
                print(f"UE context with cucp_src {cucp_src} cucp_index {cucp_index} not found. !!")
            return
        self.contexts[ue_id].tmsi = tmsi

    ####################################################################
    def get_num_contexts(self) -> int:
        return len(self.contexts)

    ####################################################################
    def __str__(self):
        return (
            f"ue_contexts_map(\n"
            f"  contexts={self.contexts},\n"
            f"  contexts_by_du_index={self.contexts_by_du_index},\n"
            f"  contexts_by_cucp_index={self.contexts_by_cucp_index},\n"
            f"  contexts_by_cuup_index={self.contexts_by_cuup_index},\n"
            f"  contexts_by_cucp_ue_e1ap_id={self.contexts_by_cucp_ue_e1ap_id},\n"
            f"  contexts_by_cuup_ue_e1ap_id={self.contexts_by_cuup_ue_e1ap_id}\n"
            f")"
        )


##########################################################################################################
if __name__ == "__main__":

    dbg = False

    s = ue_contexts_map(dbg=dbg)

    du1_src="du1"
    cucp1_src="cucp1"
    cuup1_src="cuup1"

    print("#############################################################################")
    print("# create a new UE context")
    s.hook_du_ue_ctx_creation(du1_src,
                              0,     # du_index
                              101,   # plmn
                              400,   # pci
                              20000, # crnti
                              12,    # tac
                              201)   # nci
    assert s.get_num_contexts() == 1

    print("#############################################################################")
    print("# Use same du_index.  This will overwrite the previous context")
    s.hook_du_ue_ctx_creation(du1_src,
                              0,   # du_index
                              101,   # plmn
                              401,   # pci
                              20000, # crnti
                              12,    # tac
                              201)   # nci
    assert s.get_num_contexts() == 1
    ue_id = s.getid_by_du_index(du1_src, 0)
    assert ue_id == 1
    ue = s.getue_by_id(ue_id)
    print(ue)
    assert ue is not None and ue.du_index == unique_index("du1", 0) \
        and ue.cucp_index is None and ue.cuup_index is None \
        and ue.plmn==101 and ue.nci==201 and ue.pci==401 and ue.tac==12 and ue.crnti==20000


    print("############################################################################")
    print("# Use same plmn, pci, crnti.  This will overwrite the previous context")
    s.hook_du_ue_ctx_creation(du1_src,
                              1,   # du_index
                              101,   # plmn
                              401,   # pci
                              20000, # crnti
                              12,    # tac
                              201)   # nci
    assert s.get_num_contexts() == 1
    ue_id = s.getid_by_du_index(du1_src, 1) 
    assert ue_id == 2
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==unique_index(du1_src,1) and ue.cucp_index is None and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci==201 and ue.pci==401 and ue.tac==12 and ue.crnti==20000


    print("###########################################################################")
    print("# Create 2nd UE context with different du_index")
    s.hook_du_ue_ctx_creation(du1_src,
                              2,   # du_index
                              101,   # plmn
                              401,   # pci
                              20001, # crnti
                              12,    # tac
                              201)   # nci
    assert s.get_num_contexts() == 2
    ue_id = s.getid_by_du_index(du1_src, 1) 
    assert ue_id == 2
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==unique_index(du1_src,1) and ue.cucp_index is None and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci==201 and ue.pci==401 and ue.tac==12 and ue.crnti==20000
    ue_id = s.getid_by_du_index(du1_src, 2) 
    assert ue_id == 3
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==unique_index(du1_src,2) and ue.cucp_index is None and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci==201 and ue.pci==401 and ue.tac==12 and ue.crnti==20001

    
    
    print("############################################################################")
    print("# Add a cucp UE where there is no existing context with the matching plmn, pci, crnti")
    s.hook_cucp_uemgr_ue_add(cucp1_src, 
                             0,     # cucp_index
                             101,   # plmn
                             499,   # pci
                             20000), # crnti
    assert s.get_num_contexts() == 3
    ue_id = s.getid_by_cucp_index(cucp1_src, 0)
    assert ue_id == 4
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index is None and ue.cucp_index==unique_index(cucp1_src, 0) and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci is None and ue.pci==499 and ue.tac is None and ue.crnti==20000


    print("############################################################################")
    print("# Add a cucp UE where there is an existing context with the matching plmn, pci, crnti")
    s.hook_cucp_uemgr_ue_add(cucp1_src, 
                             1,     # cucp_index
                             101,   # plmn
                             401,   # pci
                             20000), # crnti
    assert s.get_num_contexts() == 3
    ue_id = s.getid_by_cucp_index(cucp1_src, 1)
    assert ue_id == 2
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==unique_index(du1_src,1) and ue.cucp_index==unique_index(cucp1_src, 1) and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci==201 and ue.pci==401 and ue.tac==12 and ue.crnti==20000


    print("############################################################################")
    print("# Add a cucp UE where there is an existing context with the matching plmn, pci, crnti, with cucp_index != None")
    s.hook_cucp_uemgr_ue_add(cucp1_src, 
                             1,     # cucp_index
                             101,   # plmn
                             401,   # pci
                             20000), # crnti
    assert s.get_num_contexts() == 3
    ue_id = s.getid_by_cucp_index(cucp1_src, 1)
    assert ue_id == 5
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index is None and ue.cucp_index==unique_index(cucp1_src, 1) and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci is None and ue.pci==401 and ue.tac is None and ue.crnti==20000


    print("############################################################################")
    print("# Call hook_e1_cucp_bearer_context_setup top add the id to an existing UE")
    s.hook_e1_cucp_bearer_context_setup(cucp1_src, 
                                        1,    # cucp_index
                                        2000) # cucp_ue_e1ap_id
    assert s.get_num_contexts() == 3
    ue_id = s.getid_by_cucp_index(cucp1_src, 1)
    assert ue_id == 5
    ue_id = s.getid_by_cucp_ue_e1ap_id(cucp1_src, 2000)
    assert ue_id == 5
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index is None and ue.cucp_index==unique_index(cucp1_src, 1) and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci is None and ue.pci==401 and ue.tac is None and ue.crnti==20000 \
           and len(ue.e1_bearers)==1 and ue.e1_bearers[0][0]==(cucp1_src,2000) and ue.e1_bearers[0][1] is None
    
    
    print("############################################################################")
    print("# Call hook_e1_cucp_bearer_context_setup again.  Ths will delete the context")
    s.hook_e1_cucp_bearer_context_setup(cucp1_src, 
                                        1,    # cucp_index
                                        2000) # cucp_ue_e1ap_id
    assert s.get_num_contexts() == 3


    print("#############################################################################")
    print("# delete s and start fresh")
    s = ue_contexts_map(dbg=dbg)


    print("#############################################################################")
    print("# create DU UE context")
    s.hook_du_ue_ctx_creation(du1_src,
                              0,   # du_index
                              101,   # plmn
                              400,   # pci
                              20000, # crnti
                              12,    # tac
                              201)   # nci
    # create cucp context
    s.hook_cucp_uemgr_ue_add(cucp1_src, 
                             1,     # cucp_index
                             101,   # plmn
                             400,   # pci
                             20000), # crnti
    # create cucp e1ap id
    s.hook_e1_cucp_bearer_context_setup(cucp1_src, 
                                        1,    # cucp_index
                                        2000) # cucp_ue_e1ap_id
    assert s.get_num_contexts() == 1
    ue_id = s.getid_by_du_index(du1_src, 0)
    assert ue_id == 0
    ue_id = s.getid_by_cucp_index(cucp1_src, 1)
    assert ue_id == 0
    ue_id = s.getid_by_cucp_ue_e1ap_id(cucp1_src, 2000)
    assert ue_id == 0
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==unique_index(du1_src,0) and ue.cucp_index==unique_index(cucp1_src, 1) and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci==201 and ue.pci==400 and ue.tac==12 and ue.crnti==20000 \
           and len(ue.e1_bearers)==1 and ue.e1_bearers[0][0]==(cucp1_src, 2000) and ue.e1_bearers[0][1] is None


    print("#############################################################################")
    print("# add cuup e1 context")
    s.hook_e1_cuup_bearer_context_setup(cuup1_src,
                                        10,    # cuup_index
                                        2000,  # gnb_cucp_ue_e1ap_id,
                                        12000, # gnb_cuup_ue_e1ap_id
                                        True)  # succees

    assert s.get_num_contexts() == 1
    ue_id = s.getid_by_du_index(du1_src, 0)
    assert ue_id == 0
    ue_id = s.getid_by_cucp_index(cucp1_src, 1)
    assert ue_id == 0
    ue_id = s.getid_by_cucp_ue_e1ap_id(cucp1_src, 2000)
    assert ue_id == 0
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==unique_index(du1_src,0) and ue.cucp_index==unique_index(cucp1_src, 1) and ue.cuup_index==unique_index(cuup1_src,10) \
           and ue.plmn==101 and ue.nci==201 and ue.pci==400 and ue.tac==12 and ue.crnti==20000 \
           and len(ue.e1_bearers)==1 and ue.e1_bearers[0][0]==(cucp1_src,2000) and ue.e1_bearers[0][1]==(cuup1_src,12000)


    print("#############################################################################")
    print("# Try to do it again - thil cause the bearer to be deleted")
    s.hook_e1_cuup_bearer_context_setup(cuup1_src,
                                        11,    # cuup_index
                                        2000,  # gnb_cucp_ue_e1ap_id,
                                        12000, # gnb_cuup_ue_e1ap_id
                                        True)  # succees
    assert s.get_num_contexts() == 1

    
    print("#############################################################################")
    print("# delete s and start fresh")
    s = ue_contexts_map(dbg=dbg)


    print("#############################################################################")
    print("# create UE bearers, with 2 e1 bearers per ue")
    num_ue = 10
    num_e1 = 3
    crnti_off = 20000
    du_off = 100
    cucp_off = 200
    cuup_off = 300
    cucp_e1Off = 20000
    cuup_e1Off = 30000

    for ue in range(0, num_ue):
        s.hook_du_ue_ctx_creation(  du1_src, 
                                    du_off+ue,   # du_index
                                    101,   # plmn
                                    400,   # pci
                                    crnti_off+ue, # crnti
                                    12,    # tac
                                    201)   # nci
        # create cucp context
        s.hook_cucp_uemgr_ue_add(   cucp1_src, 
                                    cucp_off+ue,     # cucp_index
                                    101,   # plmn
                                    400,   # pci
                                    crnti_off+ue), # crnti
        for e1 in range(0, num_e1):
            # create cucp e1ap id
            e1off = (ue * num_e1) + e1
            s.hook_e1_cucp_bearer_context_setup(    cucp1_src, 
                                                    cucp_off+ue,    # cucp_index
                                                    cucp_e1Off+e1off) # cucp_ue_e1ap_id
            s.hook_e1_cuup_bearer_context_setup(    cuup1_src,
                                                    cuup_off+ue,    # cuup_index
                                                    cucp_e1Off+e1off,  # gnb_cucp_ue_e1ap_id,
                                                    cuup_e1Off+e1off, # gnb_cuup_ue_e1ap_id
                                                    True)  # succees

    assert s.get_num_contexts() == num_ue

    for ue in range(0, num_ue):
        ue_id = s.getid_by_du_index(du1_src, du_off+ue)
        assert ue_id == ue
        ue_id = s.getid_by_cucp_index(cucp1_src, cucp_off+ue)
        assert ue_id == ue
        ue_id = s.getid_by_cuup_index(cuup1_src, cuup_off+ue)
        assert ue_id == ue
        for e1 in range(0, num_e1):
            e1off = (ue * num_e1) + e1
            ue_id = s.getid_by_cucp_ue_e1ap_id(cucp1_src, cucp_e1Off+e1off)
            assert ue_id == ue
            ue_id = s.getid_by_cuup_ue_e1ap_id(cuup1_src, cuup_e1Off+e1off)
            assert ue_id == ue
        ctx = s.getue_by_id(ue_id)
        assert ctx is not None and ctx.du_index==unique_index(du1_src,du_off+ue) and ctx.cucp_index==unique_index(cucp1_src, cucp_off+ue) and ctx.cuup_index==unique_index(cuup1_src,cuup_off+ue) \
               and ctx.plmn==101 and ctx.nci==201 and ctx.pci==400 and ctx.tac==12 and ctx.crnti==crnti_off+ue \
               and len(ctx.e1_bearers)==num_e1 and \
               all(ctx.e1_bearers[i][0]==(cucp1_src, cucp_e1Off+(ue*num_e1)+i) and ctx.e1_bearers[i][1]==(cuup1_src, cuup_e1Off+(ue*num_e1)+i) for i in range(0, num_e1))


    print("#############################################################################")
    print("# Test accessors")
    assert s.getid_by_du_index(du1_src, du_off+0) == 0
    assert s.getid_by_du_index(du1_src, du_off+9) == 9
    assert s.getid_by_du_index(du1_src, du_off+10) is None

    assert s.getid_by_cucp_index(cucp1_src, cucp_off+0) == 0
    assert s.getid_by_cucp_index(cucp1_src, cucp_off+9) == 9
    assert s.getid_by_cucp_index(cucp1_src, cucp_off+10) is None

    assert s.getid_by_cuup_index(cuup1_src,cuup_off+0) == 0
    assert s.getid_by_cuup_index(cuup1_src,cuup_off+9) == 9
    assert s.getid_by_cuup_index(cuup1_src,cuup_off+10) is None

    assert s.getid_by_cucp_ue_e1ap_id(cucp1_src, cucp_e1Off+(0*num_e1)+0) == 0
    assert s.getid_by_cucp_ue_e1ap_id(cucp1_src, cucp_e1Off+(0*num_e1)+2) == 0
    assert s.getid_by_cucp_ue_e1ap_id(cucp1_src, cucp_e1Off+(9*num_e1)+0) == 9
    assert s.getid_by_cucp_ue_e1ap_id(cucp1_src, cucp_e1Off+(9*num_e1)+2) == 9
    assert s.getid_by_cucp_ue_e1ap_id(cucp1_src, cucp_e1Off+(10*num_e1)+0) is None

    assert s.getid_by_cuup_ue_e1ap_id(cuup1_src, cuup_e1Off+(0*num_e1)+0) == 0
    assert s.getid_by_cuup_ue_e1ap_id(cuup1_src, cuup_e1Off+(0*num_e1)+2) == 0
    assert s.getid_by_cuup_ue_e1ap_id(cuup1_src, cuup_e1Off+(9*num_e1)+0) == 9
    assert s.getid_by_cuup_ue_e1ap_id(cuup1_src, cuup_e1Off+(9*num_e1)+2) == 9
    assert s.getid_by_cuup_ue_e1ap_id(cuup1_src, cuup_e1Off+(10*num_e1)+0) is None


    print("#############################################################################")
    print("# Test deletion - du index, then cucp index, then cuup index.  Context will only be deleted when all 3 are cleared")
    ue_to_delete = num_ue-1
    ue = s.getid_by_du_index(du1_src, du_off+ue_to_delete)
    s.hook_du_ue_ctx_deletion(du1_src, du_off+ue_to_delete)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index==unique_index(cucp1_src, cucp_off+ue) and ctx.cuup_index==unique_index(cuup1_src,cuup_off+ue) \
            and ctx.plmn==101 and ctx.nci==201 and ctx.pci==400 and ctx.tac==12 and ctx.crnti==crnti_off+ue \
            and len(ctx.e1_bearers)==num_e1 and \
            all(ctx.e1_bearers[i][0]==(cucp1_src, cucp_e1Off+(ue*num_e1)+i) and ctx.e1_bearers[i][1]==(cuup1_src, cuup_e1Off+(ue*num_e1)+i) for i in range(0, num_e1))
    s.hook_cucp_uemgr_ue_remove(cucp1_src, cucp_off+ue)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index is None and ctx.cuup_index==unique_index(cuup1_src,cuup_off+ue) \
            and ctx.plmn==101 and ctx.nci==201 and ctx.pci==400 and ctx.tac==12 and ctx.crnti==crnti_off+ue \
            and len(ctx.e1_bearers)==num_e1 and \
            all(ctx.e1_bearers[i][0]==(cucp1_src, cucp_e1Off+(ue*num_e1)+i) and ctx.e1_bearers[i][1]==(cuup1_src, cuup_e1Off+(ue*num_e1)+i) for i in range(0, num_e1))
    for e1 in range(0, num_e1):
        e1off = (ue * num_e1) + e1
        s.hook_e1_cuup_bearer_context_release(cuup1_src, cuup_off+ue, cucp_e1Off+e1off, cuup_e1Off+e1off, True)
        if e1 < num_e1-1:
            assert s.get_num_contexts() == num_ue
        else:
            # context should be deleted after removing the last e1 bearer
            assert s.get_num_contexts() == num_ue-1
            num_ue = num_ue-1
    ctx = s.getue_by_id(ue)
    assert ctx is None

    
    print("###############################################################################")
    print("# Test deletion - cuup, then cucp, then du")
    ue_to_delete = num_ue-1
    ue = s.getid_by_du_index(du1_src, du_off+ue_to_delete)
    for e1 in range(0, num_e1):
        e1off = (ue * num_e1) + e1
        s.hook_e1_cuup_bearer_context_release(cuup1_src, cuup_off+ue, cucp_e1Off+e1off, cuup_e1Off+e1off, True)
        assert s.get_num_contexts() == num_ue
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==unique_index(du1_src,du_off+ue) and ctx.cucp_index==unique_index(cucp1_src, cucp_off+ue) and ctx.cuup_index is None \
        and ctx.plmn==101 and ctx.nci==201 and ctx.pci==400 and ctx.tac==12 and ctx.crnti==crnti_off+ue \
        and len(ctx.e1_bearers)==0 
    s.hook_cucp_uemgr_ue_remove(cucp1_src, cucp_off+ue)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==unique_index(du1_src,du_off+ue) and ctx.cucp_index is None and ctx.cuup_index is None \
        and ctx.plmn==101 and ctx.nci==201 and ctx.pci==400 and ctx.tac==12 and ctx.crnti==crnti_off+ue \
        and len(ctx.e1_bearers)==0 
    s.hook_du_ue_ctx_deletion(du1_src, du_off+ue)
    ctx = s.getue_by_id(ue)
    assert ctx is None


    print("#############################################################################")
    print("# delete s and start fresh")
    s = ue_contexts_map(dbg=dbg)


    print("###############################################################################")
    print("# Test 3 du, 1 cucp, 2 cuup")
    num_du = 3
    num_ue_per_du = 4
    num_cucp = 1
    num_cuup = 2
    num_e1 = 2
    num_ue = num_du * num_ue_per_du  

    ues_per_cuup = num_ue // num_cuup
    bearers_per_cuup = num_e1 * ues_per_cuup

    for ue in range(0, num_ue):
        du_id = ue // num_ue_per_du
        du_src = f"du{du_id}"
        du_index = ue % num_ue_per_du
        plmn = 101
        pci = 400 + du_id
        crnti = 30000 +  du_index
        tac = 12 + du_id
        nci = 201 + du_id
        cucp_src = "cucp0"
        cucp_index = ue // num_cucp

        # print(f"du_id {du_id} du_src {du_src} du_index {du_index} plmn {plmn} pci {pci} crnti {crnti} tac {tac} nci {nci}")
        s.hook_du_ue_ctx_creation( du_src, 
                                   du_index,   # du_index
                                   plmn,
                                   pci,
                                   crnti,
                                   tac,
                                   nci)

        # print(f"cucp_src {cucp_src} cucp_index {cucp_index}")
        s.hook_cucp_uemgr_ue_add(   cucp_src, 
                                    cucp_index,
                                    plmn,
                                    pci,
                                    crnti)

        # print(f"ue {ue} cuup_id {cuup_id} cuup_src {cuup_src} cuup_index {cuup_index}")
        for e1 in range(0, num_e1):
            cucp_ue_e1ap_id = ((ue * num_e1) + e1) 
            cuup_id = cucp_ue_e1ap_id // bearers_per_cuup
            cuup_src = f"cuup{cuup_id}"
            cuup_index = ue %  ues_per_cuup
            cuup_ue_e1ap_id = cucp_ue_e1ap_id % bearers_per_cuup

            # print(f"ue {ue} cuup_id {cuup_id} cuup_src {cuup_src} cuup_index {cuup_index} cucp_ue_e1ap_id {cucp_ue_e1ap_id} cuup_ue_e1ap_id {cuup_ue_e1ap_id}")
            s.hook_e1_cucp_bearer_context_setup(    cucp_src, 
                                                    cucp_index,   
                                                    cucp_ue_e1ap_id) 
            s.hook_e1_cuup_bearer_context_setup(    cuup_src,
                                                    cuup_index,
                                                    cucp_ue_e1ap_id,
                                                    cuup_ue_e1ap_id,
                                                    True)  # succees

    # assert the expected contexts
    expected_contexts = [
        {'du_index': {'src':'du0', 'idx':0}, 'cucp_index': {'src':'cucp0', 'idx':0}, 'cuup_index': {'src':'cuup0', 'idx':0}, 'plmn': 101, 'nci': 201, 'pci': 400, 'tac': 12, 'crnti': 30000, 'tmsi': None, 'e1_bearers': [(('cucp0', 0), ('cuup0', 0)), (('cucp0', 1), ('cuup0', 1))]},
        {'du_index': {'src':'du0', 'idx':1}, 'cucp_index': {'src':'cucp0', 'idx':1}, 'cuup_index': {'src':'cuup0', 'idx':1}, 'plmn': 101, 'nci': 201, 'pci': 400, 'tac': 12, 'crnti': 30001, 'tmsi': None, 'e1_bearers': [(('cucp0', 2), ('cuup0', 2)), (('cucp0', 3), ('cuup0', 3))]},
        {'du_index': {'src':'du0', 'idx':2}, 'cucp_index': {'src':'cucp0', 'idx':2}, 'cuup_index': {'src':'cuup0', 'idx':2}, 'plmn': 101, 'nci': 201, 'pci': 400, 'tac': 12, 'crnti': 30002, 'tmsi': None, 'e1_bearers': [(('cucp0', 4), ('cuup0', 4)), (('cucp0', 5), ('cuup0', 5))]},
        {'du_index': {'src':'du0', 'idx':3}, 'cucp_index': {'src':'cucp0', 'idx':3}, 'cuup_index': {'src':'cuup0', 'idx':3}, 'plmn': 101, 'nci': 201, 'pci': 400, 'tac': 12, 'crnti': 30003, 'tmsi': None, 'e1_bearers': [(('cucp0', 6), ('cuup0', 6)), (('cucp0', 7), ('cuup0', 7))]},
        {'du_index': {'src':'du1', 'idx':0}, 'cucp_index': {'src':'cucp0', 'idx':4}, 'cuup_index': {'src':'cuup0', 'idx':4}, 'plmn': 101, 'nci': 202, 'pci': 401, 'tac': 13, 'crnti': 30000, 'tmsi': None, 'e1_bearers': [(('cucp0', 8), ('cuup0', 8)), (('cucp0', 9), ('cuup0', 9))]},
        {'du_index': {'src':'du1', 'idx':1}, 'cucp_index': {'src':'cucp0', 'idx':5}, 'cuup_index': {'src':'cuup0', 'idx':5}, 'plmn': 101, 'nci': 202, 'pci': 401, 'tac': 13, 'crnti': 30001, 'tmsi': None, 'e1_bearers': [(('cucp0', 10), ('cuup0', 10)), (('cucp0', 11), ('cuup0', 11))]},
        {'du_index': {'src':'du1', 'idx':2}, 'cucp_index': {'src':'cucp0', 'idx':6}, 'cuup_index': {'src':'cuup1', 'idx':0}, 'plmn': 101, 'nci': 202, 'pci': 401, 'tac': 13, 'crnti': 30002, 'tmsi': None, 'e1_bearers': [(('cucp0', 12), ('cuup1', 0)), (('cucp0', 13), ('cuup1', 1))]},
        {'du_index': {'src':'du1', 'idx':3}, 'cucp_index': {'src':'cucp0', 'idx':7}, 'cuup_index': {'src':'cuup1', 'idx':1}, 'plmn': 101, 'nci': 202, 'pci': 401, 'tac': 13, 'crnti': 30003, 'tmsi': None, 'e1_bearers': [(('cucp0', 14), ('cuup1', 2)), (('cucp0', 15), ('cuup1', 3))]},
        {'du_index': {'src':'du2', 'idx':0}, 'cucp_index': {'src':'cucp0', 'idx':8}, 'cuup_index': {'src':'cuup1', 'idx':2}, 'plmn': 101, 'nci': 203, 'pci': 402, 'tac': 14, 'crnti': 30000, 'tmsi': None, 'e1_bearers': [(('cucp0', 16), ('cuup1', 4)), (('cucp0', 17), ('cuup1', 5))]},
        {'du_index': {'src':'du2', 'idx':1}, 'cucp_index': {'src':'cucp0', 'idx':9}, 'cuup_index': {'src':'cuup1', 'idx':3}, 'plmn': 101, 'nci': 203, 'pci': 402, 'tac': 14, 'crnti': 30001, 'tmsi': None, 'e1_bearers': [(('cucp0', 18), ('cuup1', 6)), (('cucp0', 19), ('cuup1', 7))]},
        {'du_index': {'src':'du2', 'idx':2}, 'cucp_index': {'src':'cucp0', 'idx':10}, 'cuup_index': {'src':'cuup1', 'idx':4}, 'plmn': 101, 'nci': 203, 'pci': 402, 'tac': 14, 'crnti': 30002, 'tmsi': None, 'e1_bearers': [(('cucp0', 20), ('cuup1', 8)), (('cucp0', 21), ('cuup1', 9))]},
        {'du_index': {'src':'du2', 'idx':3}, 'cucp_index': {'src':'cucp0', 'idx':11}, 'cuup_index': {'src':'cuup1', 'idx':5}, 'plmn': 101, 'nci': 203, 'pci': 402, 'tac': 14, 'crnti': 30003, 'tmsi': None, 'e1_bearers': [(('cucp0', 22), ('cuup1', 10)), (('cucp0', 23), ('cuup1', 11))]}
    ]
    expected_contexts_by_du_index = {'du0::0': 0, 'du0::1': 1, 'du0::2': 2, 'du0::3': 3, 'du1::0': 4, 'du1::1': 5, 'du1::2': 6, 'du1::3': 7, 'du2::0': 8, 'du2::1': 9, 'du2::2': 10, 'du2::3': 11}
    expected_contexts_by_cucp_index= {'cucp0::0': 0, 'cucp0::1': 1, 'cucp0::2': 2, 'cucp0::3': 3, 'cucp0::4': 4, 'cucp0::5': 5, 'cucp0::6': 6, 'cucp0::7': 7, 'cucp0::8': 8, 'cucp0::9': 9, 'cucp0::10': 10, 'cucp0::11': 11}
    expected_contexts_by_cuup_index= {'cuup0::0': 0, 'cuup0::1': 1, 'cuup0::2': 2, 'cuup0::3': 3, 'cuup0::4': 4, 'cuup0::5': 5, 'cuup1::0': 6, 'cuup1::1': 7, 'cuup1::2': 8, 'cuup1::3': 9, 'cuup1::4': 10, 'cuup1::5': 11}
    expected_contexts_by_cucp_ue_e1ap_id= {'cucp0::0': 0, 'cucp0::1': 0, 'cucp0::2': 1, 'cucp0::3': 1, 'cucp0::4': 2, 'cucp0::5': 2, 'cucp0::6': 3, 'cucp0::7': 3, 'cucp0::8': 4, 'cucp0::9': 4, 'cucp0::10': 5, 'cucp0::11': 5, 'cucp0::12': 6, 'cucp0::13': 6, 'cucp0::14': 7, 'cucp0::15': 7, 'cucp0::16': 8, 'cucp0::17': 8, 'cucp0::18': 9, 'cucp0::19': 9, 'cucp0::20': 10, 'cucp0::21': 10, 'cucp0::22': 11, 'cucp0::23': 11}
    expected_contexts_by_cuup_ue_e1ap_id= {'cuup0::0': 0, 'cuup0::1': 0, 'cuup0::2': 1, 'cuup0::3': 1, 'cuup0::4': 2, 'cuup0::5': 2, 'cuup0::6': 3, 'cuup0::7': 3, 'cuup0::8': 4, 'cuup0::9': 4, 'cuup0::10': 5, 'cuup0::11': 5, 'cuup1::0': 6, 'cuup1::1': 6, 'cuup1::2': 7, 'cuup1::3': 7, 'cuup1::4': 8, 'cuup1::5': 8, 'cuup1::6': 9, 'cuup1::7': 9, 'cuup1::8': 10, 'cuup1::9': 10, 'cuup1::10': 11, 'cuup1::11': 11}

    for i in range(0, num_ue):
        ctx = s.getue_by_id(i)
        assert asdict(ctx) == expected_contexts[i]

    contexts_by_du_index = {f"{k.src}::{k.idx}": v for k, v in s.contexts_by_du_index.items()}
    assert contexts_by_du_index == expected_contexts_by_du_index

    contexts_by_cucp_index = {f"{k.src}::{k.idx}": v for k, v in s.contexts_by_cucp_index.items()}
    assert contexts_by_cucp_index == expected_contexts_by_cucp_index

    contexts_by_cuup_index = {f"{k.src}::{k.idx}": v for k, v in s.contexts_by_cuup_index.items()}
    assert contexts_by_cuup_index == expected_contexts_by_cuup_index

    contexts_by_cucp_ue_e1ap_id = {f"{k[0]}::{k[1]}": v for k, v in s.contexts_by_cucp_ue_e1ap_id.items()}
    assert contexts_by_cucp_ue_e1ap_id == expected_contexts_by_cucp_ue_e1ap_id

    contexts_by_cuup_ue_e1ap_id = {f"{k[0]}::{k[1]}": v for k, v in s.contexts_by_cuup_ue_e1ap_id.items()}
    assert contexts_by_cuup_ue_e1ap_id == expected_contexts_by_cuup_ue_e1ap_id

    print("#############################################################################")
    print("# Test accessors")
    assert s.getid_by_du_index('du0', 0) == 0
    assert s.getid_by_du_index('du0', 1) == 1
    assert s.getid_by_du_index('du0', 2) == 2
    assert s.getid_by_du_index('du0', 3) == 3
    assert s.getid_by_du_index('du1', 0) == 4
    assert s.getid_by_du_index('du1', 1) == 5
    assert s.getid_by_du_index('du1', 2) == 6
    assert s.getid_by_du_index('du1', 3) == 7
    assert s.getid_by_du_index('du2', 0) == 8
    assert s.getid_by_du_index('du2', 1) == 9
    assert s.getid_by_du_index('du2', 2) == 10
    assert s.getid_by_du_index('du2', 3) == 11
    assert s.getid_by_du_index('du0', 4) is None
    assert s.getid_by_du_index('du1', 4) is None
    assert s.getid_by_du_index('du2', 4) is None
    assert s.getid_by_du_index('du3', 0) is None

    assert s.getid_by_cucp_index('cucp0', 0) == 0
    assert s.getid_by_cucp_index('cucp0', 1) == 1
    assert s.getid_by_cucp_index('cucp0', 2) == 2
    assert s.getid_by_cucp_index('cucp0', 3) == 3
    assert s.getid_by_cucp_index('cucp0', 4) == 4
    assert s.getid_by_cucp_index('cucp0', 5) == 5
    assert s.getid_by_cucp_index('cucp0', 6) == 6
    assert s.getid_by_cucp_index('cucp0', 7) == 7
    assert s.getid_by_cucp_index('cucp0', 8) == 8
    assert s.getid_by_cucp_index('cucp0', 9) == 9
    assert s.getid_by_cucp_index('cucp0', 10) == 10
    assert s.getid_by_cucp_index('cucp0', 11) == 11
    assert s.getid_by_cucp_index('cucp0', 12) == None

    assert s.getid_by_cuup_index('cuup0', 0) == 0
    assert s.getid_by_cuup_index('cuup0', 1) == 1
    assert s.getid_by_cuup_index('cuup0', 2) == 2
    assert s.getid_by_cuup_index('cuup0', 3) == 3
    assert s.getid_by_cuup_index('cuup0', 4) == 4
    assert s.getid_by_cuup_index('cuup0', 5) == 5
    assert s.getid_by_cuup_index('cuup1', 0) == 6
    assert s.getid_by_cuup_index('cuup1', 1) == 7
    assert s.getid_by_cuup_index('cuup1', 2) == 8
    assert s.getid_by_cuup_index('cuup1', 3) == 9
    assert s.getid_by_cuup_index('cuup1', 4) == 10
    assert s.getid_by_cuup_index('cuup1', 5) == 11
    assert s.getid_by_cuup_index('cuup0', 6) == None
    assert s.getid_by_cuup_index('cuup1', 6) == None
    assert s.getid_by_cuup_index('cuup2',0) == None

    assert s.getid_by_cucp_ue_e1ap_id('cucp0', 0) == 0
    assert s.getid_by_cucp_ue_e1ap_id('cucp0', 1) == 0
    assert s.getid_by_cucp_ue_e1ap_id('cucp0', 2) == 1
    assert s.getid_by_cucp_ue_e1ap_id('cucp0', 3) == 1
    assert s.getid_by_cucp_ue_e1ap_id('cucp0', 20) == 10
    assert s.getid_by_cucp_ue_e1ap_id('cucp0', 21) == 10
    assert s.getid_by_cucp_ue_e1ap_id('cucp0', 22) == 11
    assert s.getid_by_cucp_ue_e1ap_id('cucp0', 23) == 11
    assert s.getid_by_cucp_ue_e1ap_id('cucp0', 24) is None

    assert s.getid_by_cuup_ue_e1ap_id('cuup0', 0) == 0
    assert s.getid_by_cuup_ue_e1ap_id('cuup0', 1) == 0
    assert s.getid_by_cuup_ue_e1ap_id('cuup0', 10) == 5
    assert s.getid_by_cuup_ue_e1ap_id('cuup0', 11) == 5
    assert s.getid_by_cuup_ue_e1ap_id('cuup0', 12) == None
    assert s.getid_by_cuup_ue_e1ap_id('cuup1', 0) == 6
    assert s.getid_by_cuup_ue_e1ap_id('cuup1', 1) == 6
    assert s.getid_by_cuup_ue_e1ap_id('cuup1', 10) == 11
    assert s.getid_by_cuup_ue_e1ap_id('cuup1', 11) == 11
    assert s.getid_by_cuup_ue_e1ap_id('cuup1', 12) == None
    
    print("#############################################################################")
    print("# Test deletion - du index, then cucp index, then cuup index.  Context will only be deleted when all 3 are cleared")

    ue = s.getid_by_du_index('du2', 3)
    s.hook_du_ue_ctx_deletion('du2', 3)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index==unique_index('cucp0', 11) and ctx.cuup_index==unique_index('cuup1', 5) \
            and ctx.plmn==101 and ctx.nci==203 and ctx.pci==402 and ctx.tac==14 and ctx.crnti==30003 \
            and len(ctx.e1_bearers)==2 \
            and ctx.e1_bearers[0][0]==('cucp0', 22) and ctx.e1_bearers[0][1]==('cuup1', 10) and ctx.e1_bearers[1][0]==('cucp0', 23) and ctx.e1_bearers[1][1]==('cuup1', 11)
    
    s.hook_cucp_uemgr_ue_remove('cucp0', 11)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index is None and ctx.cuup_index==unique_index('cuup1', 5) \
            and ctx.plmn==101 and ctx.nci==203 and ctx.pci==402 and ctx.tac==14 and ctx.crnti==30003 \
            and len(ctx.e1_bearers)==2 \
            and ctx.e1_bearers[0][0]==('cucp0', 22) and ctx.e1_bearers[0][1]==('cuup1', 10) and ctx.e1_bearers[1][0]==('cucp0', 23) and ctx.e1_bearers[1][1]==('cuup1', 11)
   
    # try an e1ap_ids=22/13.   e1ap_id=13 is not known so nothing should happen
    s.hook_e1_cuup_bearer_context_release('cuup1', 5, 22, 13, True)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index is None and ctx.cuup_index==unique_index('cuup1', 5) \
            and ctx.plmn==101 and ctx.nci==203 and ctx.pci==402 and ctx.tac==14 and ctx.crnti==30003 \
            and len(ctx.e1_bearers)==2 \
            and ctx.e1_bearers[0][0]==('cucp0', 22) and ctx.e1_bearers[0][1]==('cuup1', 10) and ctx.e1_bearers[1][0]==('cucp0', 23) and ctx.e1_bearers[1][1]==('cuup1', 11)

    # delete 22/10. 
    s.hook_e1_cuup_bearer_context_release('cuup1', 5, 22, 10, True)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index is None and ctx.cuup_index==unique_index('cuup1', 5) \
            and ctx.plmn==101 and ctx.nci==203 and ctx.pci==402 and ctx.tac==14 and ctx.crnti==30003 \
            and len(ctx.e1_bearers)==1 \
            and ctx.e1_bearers[0][0]==('cucp0', 23) and ctx.e1_bearers[0][1]==('cuup1', 11)

    # delete 23/11 - this will delete the context
    s.hook_e1_cuup_bearer_context_release('cuup1', 5, 23, 11, True)
    ctx = s.getue_by_id(ue)
    assert ctx is None
    assert s.get_num_contexts() == 11

    print("###############################################################################")
    print("# Test deletion - cuup, then cucp, then du")

    ue = s.getid_by_du_index('du1', 0)

    s.hook_e1_cuup_bearer_context_release('cuup0', 4, 9, 9, True)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==unique_index('du1', 0) and ctx.cucp_index==unique_index('cucp0', 4) and ctx.cuup_index==unique_index('cuup0', 4) \
            and ctx.plmn==101 and ctx.nci==202 and ctx.pci==401 and ctx.tac==13 and ctx.crnti==30000 \
            and len(ctx.e1_bearers)==1 \
            and ctx.e1_bearers[0][0]==('cucp0', 8) and ctx.e1_bearers[0][1]==('cuup0', 8)

    s.hook_e1_cuup_bearer_context_release('cuup0', 4, 8, 8, True)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==unique_index('du1', 0) and ctx.cucp_index==unique_index('cucp0', 4) and ctx.cuup_index is None \
            and ctx.plmn==101 and ctx.nci==202 and ctx.pci==401 and ctx.tac==13 and ctx.crnti==30000 \
            and len(ctx.e1_bearers)==0
             
    s.hook_cucp_uemgr_ue_remove('cucp0', 4)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==unique_index('du1', 0) and ctx.cucp_index is None and ctx.cuup_index is None \
            and ctx.plmn==101 and ctx.nci==202 and ctx.pci==401 and ctx.tac==13 and ctx.crnti==30000 \
            and len(ctx.e1_bearers)==0

    s.hook_du_ue_ctx_deletion('du1', 0)
    ctx = s.getue_by_id(ue)
    assert ctx is None
    assert s.get_num_contexts() == 10      


    print("#############################################################################")
    print("# delete s and start fresh")
    s = ue_contexts_map(dbg=dbg)


    print("#############################################################################")
    print("# Test example")
    #   hook_du_ue_ctx_creation: du_index 0 tac 1 nrcgi=[ plmn=61712 nci=6733824 ] pci 1 tc_rnti 17922
    #   hook_cucp_uemgr_ue_add: cu_cp_index 1 plmn 00101 pci=1 rnti=17922
    #   hook_e1_cucp_bearer_context_setup, cu_cp_index=1 gnb_cu_cp_ue_e1ap_id=1
    #   hook_e1_cuup_bearer_context_setup success, cu_up_index 0  gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
    #   hook_e1_cuup_bearer_context_release success cu_up_index=0 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
    #   hook_du_ue_ctx_deletion: du_index 0
    #   hook_cucp_uemgr_ue_remove: cu_cp_index 1

    du_src = "du0"
    du_index = 0
    plmn = 61712
    pci = 1
    crnti = 17922
    tac = 1
    nci = 6733824
    cucp_src = "cucp0"
    cucp_index = 1
    cuup_src = "cuup0"  
    cuup_index = 0
    cucp_ue_e1ap_id=1 
    cuup_ue_e1ap_id=1

    # print(f"du_src {du_src} du_index {du_index} plmn {plmn} pci {pci} crnti {crnti} tac {tac} nci {nci}")

    assert s.get_num_contexts() == 0

    s.hook_du_ue_ctx_creation( du_src, 
                               du_index,   # du_index
                               plmn,
                               pci,
                               crnti,
                               tac,
                               nci)
    assert s.get_num_contexts() == 1
    

    s.hook_cucp_uemgr_ue_add(  cucp_src, 
                               cucp_index,
                               plmn,
                               pci,
                               crnti)
    assert s.get_num_contexts() == 1
    
    
    s.hook_e1_cucp_bearer_context_setup(    cucp_src, 
                                            cucp_index,   
                                            cucp_ue_e1ap_id) 
    assert s.get_num_contexts() == 1

    s.hook_e1_cuup_bearer_context_setup(    cuup_src,
                                            cuup_index,
                                            cucp_ue_e1ap_id,
                                            cuup_ue_e1ap_id,
                                            True)  # succees
    assert s.get_num_contexts() == 1
    

    ue = s.getid_by_du_index(du_src, du_index)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==unique_index(du_src, du_index) and ctx.cucp_index==unique_index(cucp_src, cucp_index) and ctx.cuup_index==unique_index(cuup_src, cuup_index) \
        and ctx.plmn==plmn and ctx.nci==nci and ctx.pci==pci and ctx.tac==tac and ctx.crnti==crnti \
        and len(ctx.e1_bearers)==1 \
        and ctx.e1_bearers[0][0]==(cucp_src, cucp_ue_e1ap_id) and ctx.e1_bearers[0][1]==(cuup_src, cuup_ue_e1ap_id) 
    assert s.get_num_contexts() == 1

    s.hook_e1_cuup_bearer_context_release(cuup_src, cuup_index, cucp_ue_e1ap_id, cuup_ue_e1ap_id, True)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==unique_index(du_src, du_index) and ctx.cucp_index==unique_index(cucp_src, cucp_index) and ctx.cuup_index is None \
        and ctx.plmn==plmn and ctx.nci==nci and ctx.pci==pci and ctx.tac==tac and ctx.crnti==crnti \
        and len(ctx.e1_bearers)==0
    assert s.get_num_contexts() == 1

    s.hook_du_ue_ctx_deletion(du_src, du_index)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index==unique_index(cucp_src, cucp_index) and ctx.cuup_index is None \
        and ctx.plmn==plmn and ctx.nci==nci and ctx.pci==pci and ctx.tac==tac and ctx.crnti==crnti \
        and len(ctx.e1_bearers)==0
    assert s.get_num_contexts() == 1

    s.hook_cucp_uemgr_ue_remove(cucp_src, cucp_index)
    ctx = s.getue_by_id(ue)
    assert ctx is None
    assert s.get_num_contexts() == 0


    print("#############################################################################")
    print("# Test update crnti")
    s.hook_du_ue_ctx_creation( du_src, 
                               du_index,   # du_index
                               plmn,
                               pci,
                               crnti,
                               tac,
                               nci)
    s.hook_cucp_uemgr_ue_add(  cucp_src, 
                               cucp_index,
                               plmn,
                               pci,
                               crnti)
    s.hook_e1_cucp_bearer_context_setup(    cucp_src, 
                                            cucp_index,   
                                            cucp_ue_e1ap_id) 
    s.hook_e1_cuup_bearer_context_setup(    cuup_src,
                                            cuup_index,
                                            cucp_ue_e1ap_id,
                                            cuup_ue_e1ap_id,
                                            True)  # succees
    ue = s.getid_by_du_index(du_src, du_index)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==unique_index(du_src, du_index) and ctx.cucp_index==unique_index(cucp_src, cucp_index) and ctx.cuup_index==unique_index(cuup_src, cuup_index) \
        and ctx.plmn==plmn and ctx.nci==nci and ctx.pci==pci and ctx.tac==tac and ctx.crnti==crnti \
        and len(ctx.e1_bearers)==1 \
        and ctx.e1_bearers[0][0]==(cucp_src, cucp_ue_e1ap_id) and ctx.e1_bearers[0][1]==(cuup_src, cuup_ue_e1ap_id) 
    assert s.get_num_contexts() == 1

    new_crnti = 40000

    # this one should fail as the du_index is unknown
    s.hook_du_ue_ctx_update_crnti(du_src, du_index+1, new_crnti)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==unique_index(du_src, du_index) and ctx.cucp_index==unique_index(cucp_src, cucp_index) and ctx.cuup_index==unique_index(cuup_src, cuup_index) \
        and ctx.plmn==plmn and ctx.nci==nci and ctx.pci==pci and ctx.tac==tac and ctx.crnti==crnti \
        and len(ctx.e1_bearers)==1 \
        and ctx.e1_bearers[0][0]==(cucp_src, cucp_ue_e1ap_id) and ctx.e1_bearers[0][1]==(cuup_src, cuup_ue_e1ap_id) 
    assert s.get_num_contexts() == 1

    # this one should change the crnti
    s.hook_du_ue_ctx_update_crnti(du_src, du_index, new_crnti)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==unique_index(du_src, du_index) and ctx.cucp_index==unique_index(cucp_src, cucp_index) and ctx.cuup_index==unique_index(cuup_src, cuup_index) \
        and ctx.plmn==plmn and ctx.nci==nci and ctx.pci==pci and ctx.tac==tac and ctx.crnti==new_crnti \
        and len(ctx.e1_bearers)==1 \
        and ctx.e1_bearers[0][0]==(cucp_src, cucp_ue_e1ap_id) and ctx.e1_bearers[0][1]==(cuup_src, cuup_ue_e1ap_id) 
    assert s.get_num_contexts() == 1

    print("#############################################################################")
    print("# Test getid_by_pci_rnti")
    assert s.getid_by_pci_rnti(1, new_crnti) == 1
    assert s.getid_by_pci_rnti(5, new_crnti) == 1           # incorrect pci.  just find on rnti
    assert s.getid_by_pci_rnti(1, new_crnti+1) is None      # incorrect rnti

    print("#############################################################################")
    print("# Test add_tmsi")

    assert s.getuectx(None) == None
    s.add_tmsi('cucp0', 0, 1234)   ## ue wont be found
    assert s.get_num_contexts() == 1
    s.add_tmsi('cucp0', 1, 1234)  
    u = s.getuectx(1)
    assert asdict(u) == {'du_index': {'src':'du0', 'idx':0}, 'cucp_index': {'src':'cucp0', 'idx':1}, 'cuup_index': {'src':'cuup0', 'idx':0}, 'plmn': 61712, 'nci': 6733824, 'pci': 1, 'tac': 1, 'crnti': 40000, 'tmsi': 1234, 'e1_bearers': [(('cucp0', 1), ('cuup0', 1))]}
         
    print("\n\n------ All tests passed ---------")

    sys.exit(0)
