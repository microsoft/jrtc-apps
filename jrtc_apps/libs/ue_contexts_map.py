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
    # typedef struct {
    #     uint8_t used;      /* Is the window used, 0 = not-used, 1 = used */
    #     uint32_t pkts;     /* Total packets */
    #     uint32_t bytes;    /* Total bytes*/
    # } jbpf_queue_info_t;

    # struct jbpf_pdcp_ctx_info {
    #     uint16_t ctx_id;   /* Context id (could be implementation specific) */
    #     uint32_t cu_ue_index;   /* if is_srb=True is cu_cp_ue_index, if is_srb=False is cu_up_ue_index */
    #     uint8_t is_srb; /* true=srb, false=drb */
    #     uint8_t rb_id;   /* if is_srb=True:    0=srb0, 1=srb1, 2=srb2,
    #                         if is_srb=False:   1=drb1, 2=drb2, 3-drb3 ... */
    #     uint8_t rlc_mode;  /* 0=UM, 1=AM*/

    #     // window details
    #     jbpf_queue_info_t window_info;  /* Window info */
    # };  
#     
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
from dataclasses import dataclass, asdict, replace
from typing import List, Tuple, Dict
from enum import IntEnum
import datetime as dt


##########################################
class JbpfNgapProcedure(IntEnum):
    NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP = 1
    NGAP_PROCEDURE_UE_CONTEXT_RELEASE = 2
    NGAP_PROCEDURE_PDU_SESSION_SETUP = 3
    NGAP_PROCEDURE_PDU_SESSION_MODIFY = 4
    NGAP_PROCEDURE_PDU_SESSION_RELEASE = 5
    NGAP_PROCEDURE_RESOURCE_ALLOCATION = 6
    NGAP_PROCEDURE_MAX = 7

def ngap_procedure_to_str(proc: int) -> str:
    try:
        return JbpfNgapProcedure(proc).name
    except ValueError:
        return "UNKNOWN"


##########################################
class JbpRrcProcedure(IntEnum):
    RRC_PROCEDURE_SETUP = 1
    RRC_PROCEDURE_RECONFIGURATION = 2
    RRC_PROCEDURE_REESTABLISHMENT = 3
    RRC_PROCEDURE_UE_CAPABILITY = 4
    
def rrc_procedure_to_str(proc: int) -> str:
    try:
        return JbpRrcProcedure(proc).name
    except ValueError:
        return "UNKNOWN"

##########################################
@dataclass(frozen=True)
class UniqueIndex:
    src: str
    idx: int

    def __str__(self):
        return f'{{"src":"{self.src}", "idx":{self.idx}}}'

##########################################
# The following are the group of identifiers that, as a group, are used to uniquely identify a UE at both DU and CUCP.
@dataclass(frozen=True)
class RanUniqueUeId:
    plmn: int
    pci: int
    crnti: int

    def __str__(self):
        return f'{{"plmn":"{self.plmn}", "pci":{self.pci}, "crnti":{self.crnti}}}'

@dataclass(frozen=True)
class RanNgapUeIds:
    ran_ue_ngap_id: int = None
    amf_ue_ngap_id: int = None 
       
    def __str__(self):
        return f'{{"ran_ue_ngap_id":"{self.ran_ue_ngap_id}", "amf_ue_ngap_id":{self.amf_ue_ngap_id}}}'

@dataclass(frozen=True)
class CoreGUTI:
    plmn_id: str
    amf_id: str
    mtmsi: int 

@dataclass(frozen=True)
class CoreCGI:
    plmn_id: str
    cell_id: str

@dataclass(frozen=True)
class CoreTAI:
    plmn_id: str
    tac: str

@dataclass(frozen=True)
class CoreAMFInfo:  
    suci: str = None 
    supi: str = None
    home_plmn_id: str = None
    current_guti: CoreGUTI = None
    next_guti: CoreGUTI = None
    tai: CoreTAI = None
    cgi: CoreCGI = None
    ngap_ids: RanNgapUeIds = None 

@dataclass
class UeContext:
    du_index: UniqueIndex
    cucp_index: UniqueIndex
    cuup_index: UniqueIndex
    ran_unique_ue_id: RanUniqueUeId 
    nci: int
    tac: int
    e1_bearers: List[Tuple[int, int]]     # tuple of (cucp_ue_e1ap_id, cuup_ue_e1ap_id)
    tmsi: int = None  
    ngap_ids: RanNgapUeIds = None 
    core_amf_context_index: int = None
    core_amf_info: CoreAMFInfo = None

    def __init__(self, ran_unique_ue_id: RanUniqueUeId, du_index: UniqueIndex = None, cucp_index: UniqueIndex = None, cuup_index: UniqueIndex = None,
                 nci: int = None, tac: int = None):
        self.ran_unique_ue_id = ran_unique_ue_id
        # optional
        self.nci = nci
        self.tac = tac
        self.du_index = du_index
        self.cucp_index = cucp_index
        self.cuup_index = cuup_index
        self.e1_bearers = []
        self.ngap_ids = None

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

    def get_bearer(self, cucp_ue_e1ap_id: UniqueIndex) -> Tuple[Tuple[str, int], Tuple[str, int]]:
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
                f"ran_unique_ue_id={self.ran_unique_ue_id}, nci={self.nci}, "
                f"tac={self.tac}, tmsi={self.tmsi}, "
                f"e1_bearers={self.e1_bearers}, "
                f"ngap_ids={self.ngap_ids},"
                f"core_amf_context_index={self.core_amf_context_index}, "
                f"core_amf_info={self.core_amf_info})")

    def concise_dict(self) -> Dict:

        d = asdict(self)

        # Remove internal mapping fields
        d.pop("core_amf_context_index", None)

        # Remove keys with None values
        [d.pop(k) for k in list(d) if d[k] is None]

        # remove e1_beaerss if it is empty
        if "e1_bearers" in d and len(d["e1_bearers"]) == 0:
            d.pop("e1_bearers")

        return d

###########################################################################################################
class UeContextsMap:
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
        self.amf_context_id = 0 # will just increase by 1 for each new AMF context.  No need to handle wrap as we'll never reach that
        self.amf_contexts = {}
        self.amf_tmsi_expiry_secs = dt.timedelta(seconds=21600)  # 6 hours

    ####################################################################
    def context_create(self, ran_unique_ue_id: RanUniqueUeId, du_index: UniqueIndex = None, cucp_index: UniqueIndex = None, cuup_index: UniqueIndex = None,
        nci: int=None, tac: int=None) -> None:
        if self.dbg:
            print(f"context_create: ran_unique_ue_id={ran_unique_ue_id} du_index={du_index} cucp_index={cucp_index} cuup_index={cuup_index} nci={nci} tac={tac}")
        ue = UeContext(ran_unique_ue_id, du_index=du_index, cucp_index=cucp_index, cuup_index=cuup_index, nci=nci, tac=tac)
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

    ###################################################################
    def associate_ue_context_with_amf_ngap(self, ue_id: int) -> None:

        if self.dbg:
            print(f"associate_ue_context_with_amf_ngap: ue_id={ue_id}")

        if ue_id is None:
            return

        ue = self.getue_by_id(ue_id)

        if ue.ngap_ids is None:
            # cannot assocate as no NGAP Ids
            return

        # get amf
        amf_id = self.get_amfid_by_ngap_ids(ue.ngap_ids)
        if amf_id is None:
            # no AMF context found
            return

        # to ensure consistency, disassociate the currently linked UE.
        ue2_id = self.amf_contexts[amf_id][0]
        if (ue2_id is not None) and (ue_id != ue2_id):
            ue2 = self.getue_by_id(ue2_id)
            self.disassociate_amf_context_with_ue(ue2)

        # point to AMF from UE
        ue.core_amf_context_index = amf_id
        ue.core_amf_info = self.amf_contexts[amf_id][1]  # the second element in the tuple is the CoreAMFInfo

        # point to UE from AMF
        new_t = (ue_id, self.amf_contexts[amf_id][1], None)
        self.amf_contexts[amf_id] = new_t

    ###################################################################
    def associate_ue_context_with_amf_tmsi(self, ue_id: int) -> None:

        if self.dbg:
            print(f"associate_ue_context_with_amf_tmsi: ue_id={ue_id}")

        if ue_id is None:
            return

        ue = self.getue_by_id(ue_id)

        if ue.tmsi is None:
            # cannot assocate as no TMSI
            return

        # get amf
        amf_id = self.get_amfid_by_tmsi(ue.tmsi)
        if amf_id is None:
            # no AMF context found
            return

        # to ensure consistency, disassociate the currently linked UE.
        ue2_id = self.amf_contexts[amf_id][0]
        if (ue2_id is not None) and (ue_id != ue2_id):
            ue2 = self.getue_by_id(ue2_id)
            self.disassociate_amf_context_with_ue(ue2)

        # point to AMF from UE
        ue.core_amf_context_index = amf_id
        ue.core_amf_info = self.amf_contexts[amf_id][1]  # the second element in the tuple is the CoreAMFInfo

        # point to UE from AMF
        new_t = (ue_id, self.amf_contexts[amf_id][1], None)
        self.amf_contexts[amf_id] = new_t

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

            # remove associated AMF context if it exists
            if ue.core_amf_context_index is not None:
                self.disassociate_amf_context_with_ue(ue)

    ####################################################################
    def delete_unused_context(self, ue_id: int) -> None:
        if ue_id in self.contexts:
            if self.contexts[ue_id].used():
                return
            if self.dbg:
                print(f"delete_unused_context: ue_id={ue_id}")
            ue = self.contexts[ue_id]
            self.contexts.pop(ue_id, None)

            # remove associated AMF context if it exists
            if ue.core_amf_context_index is not None:
                self.disassociate_amf_context_with_ue(ue)

    ####################################################################
    def amf_context_create_update(self, 
                ran_ue_ngap_id: int = None, amf_ue_ngap_id: int = None,
                suci: str = None, supi: str = None, home_plmn_id: str = None,
                current_guti_plmn: str = None, current_guti_amf_id: str = None, current_guti_m_tmsi: int = None,
                next_guti_plmn: str = None, next_guti_amf_id: str = None, next_guti_m_tmsi: int = None,
                tai_plmn: str = None, tai_tac: str = None,
                cgi_plmn: str = None, cgi_cellid: str = None) -> None:

        if self.dbg:
            print(f"amf_context_create_update")
        
        # get AMF context by any of the unique identifying parameters
        amf_context_id = self.get_amfid_by_core_amf_info(suci, supi, 
                               current_guti_plmn, current_guti_amf_id, current_guti_m_tmsi,
                               next_guti_plmn, next_guti_amf_id, next_guti_m_tmsi)
        
        amf_info = CoreAMFInfo(
            suci=suci,
            supi=supi,
            home_plmn_id=home_plmn_id,
            current_guti=None if current_guti_plmn is None or current_guti_amf_id is None or current_guti_m_tmsi is None else  \
                        CoreGUTI(plmn_id=current_guti_plmn, amf_id=current_guti_amf_id, mtmsi=current_guti_m_tmsi),
            next_guti=None if next_guti_plmn is None or next_guti_amf_id is None or next_guti_m_tmsi is None else  \
                        CoreGUTI(plmn_id=next_guti_plmn, amf_id=next_guti_amf_id, mtmsi=next_guti_m_tmsi),
            tai=None if tai_plmn is None or tai_tac is None else CoreTAI(plmn_id=tai_plmn, tac=tai_tac), 
            cgi=None if cgi_plmn is None or cgi_cellid is None else CoreCGI(plmn_id=cgi_plmn, cell_id=cgi_cellid),
            ngap_ids=None if ran_ue_ngap_id is None else RanNgapUeIds(ran_ue_ngap_id, amf_ue_ngap_id)
        )

        if amf_context_id is None:
            # add a new one
            amf_context_id = self.amf_context_id
            self.amf_context_id += 1

        else:

            # update the existing one
            t = self.amf_contexts[amf_context_id]

            # to ensure consistency, disassociate the currently linked UE.
            ue_id = t[0]
            if ue_id is not None:
                ue = self.getue_by_id(ue_id)
                self.disassociate_amf_context_with_ue(ue)

        # tuple is ue_context_id, amf_info
        self.amf_contexts[amf_context_id] = (None, amf_info, None)

        # Associate AMF with UE context.
        # Try NGAP-Ids, the TMSI
        if self.associate_amf_context_with_ue_ngap(amf_context_id) is False:
            self.associate_amf_context_with_ue_tmsi(amf_context_id)

    ####################################################################
    def amf_context_delete(self, amf_context_id = int) -> None:
        if self.dbg:
            print(f"amf_context_delete: amf_context_id={amf_context_id}")
        
        if amf_context_id is None:
            return
        
        t = self.amf_contexts[amf_context_id]

        # dis-associate from UE context if it exists
        if t[0] is not None:
            ue_context_id = t[0]
            ue = self.contexts[ue_context_id]
            ue.core_amf_context_index = None
            ue.core_amf_info = None

        self.amf_contexts.pop(amf_context_id, None)

    ###################################################################
    def associate_amf_context_with_ue_ngap(self, amf_context_id: int) -> bool:

        if self.dbg:
            print(f"associate_amf_context_with_ue_ngap: amf_context_id={amf_context_id}")

        t = self.amf_contexts[amf_context_id]

        if t[1].ngap_ids is not None:

            # find ue
            ueid = self.getid_by_ngap_ue_ids(t[1].ngap_ids.ran_ue_ngap_id, t[1].ngap_ids.amf_ue_ngap_id)

            if ueid is not None:
                self.amf_contexts[amf_context_id] = (ueid, t[1], None)  # update the ue_context_id in the tuple

                # update UE with the AMF context ID
                ue = self.contexts[ueid]
                ue.core_amf_context_index = amf_context_id
                ue.core_amf_info = t[1] 

                return True

        return False

    ###################################################################
    def associate_amf_context_with_ue_tmsi(self, amf_context_id: int) -> bool:

        if self.dbg:
            print(f"associate_amf_context_with_ue_tmsi: amf_context_id={amf_context_id}")

        t = self.amf_contexts[amf_context_id]

        if t[1] is None:
            return False

        # Try currrent_guti then next_guti
        for guti in [t[1].current_guti, t[1].next_guti]:
            if guti is not None:

                # find ue
                ueid = self.getid_by_tmsi(guti.mtmsi)

                if ueid is not None:
                    self.amf_contexts[amf_context_id] = (ueid, t[1], None)  # update the ue_context_id in the tuple

                    # update UE with the AMF context ID
                    ue = self.contexts[ueid]
                    ue.core_amf_context_index = amf_context_id
                    ue.core_amf_info = t[1] 

                    return True

        return False

    ###################################################################
    def disassociate_amf_context_with_ue(self, ue: UeContext) -> None:

        if ue is None:
            return

        if self.dbg:
            print(f"disassociate_amf_context_with_ue: amf_context_id={ue.core_amf_context_index}")

        t = self.amf_contexts[ue.core_amf_context_index]

        self.amf_contexts[ue.core_amf_context_index] = (None, t[1], self.now)  # update the ue_context_id in the tuple

        # update UE to clear the AMF context ID
        ue.core_amf_context_index = None
        ue.core_amf_info = None

    ####################################################################
    def set_du_index(self, ue_id: int, du_index: UniqueIndex) -> None:
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
    def set_cucp_index(self, ue_id: int, cucp_index: UniqueIndex) -> None:
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
    def set_cuup_index(self, ue_id: int, cuup_index: UniqueIndex) -> None:
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
    def set_cucp_ue_e1ap_id(self, ue_id: int, cucp_ue_e1ap_id: UniqueIndex) -> None:
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
    def clear_cucp_ue_e1ap_id(self, ue_id: int, cucp_ue_e1ap_id: UniqueIndex) -> None:
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
    def set_cuup_ue_e1ap_id(self, ue_id: int, cucp_ue_e1ap_id: UniqueIndex, cuup_ue_e1ap_id: UniqueIndex) -> None:
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
    def clear_cuup_ue_e1ap_id(self, ue_id: int, cuup_ue_e1ap_id: UniqueIndex) -> None:
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
    def getid_by_ran_unique_ue_id(self, ran_unique_ue_id: RanUniqueUeId ) -> int:
        filtered_contexts = {
            k: v for k, v in self.contexts.items()
            if v.ran_unique_ue_id == ran_unique_ue_id
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
            if v.ran_unique_ue_id.crnti == rnti
            # TBD : add pci too
        }
        if len(filtered_contexts) == 1:
            return list(filtered_contexts.keys())[0]

        # if we reach here, it means no context or >=2 was found
        return None 

    #####################################################################
    def getue_by_id(self, ue_id: int) -> UeContext:
        return self.contexts.get(ue_id, None)
    
    #####################################################################
    def getuectx(self, ue_id: int) -> UeContext:
        if ue_id is None:
            return None
        if ue_id not in self.contexts:
            if self.dbg:
                print(f"getuectx: UE context with ID {ue_id} does not exist.")
            return None
        return self.contexts[ue_id]

    #####################################################################
    def getid_by_du_index(self, du_src: str, du_index: int) -> int:
        du_index = UniqueIndex(du_src, du_index)
        return self.contexts_by_du_index.get(du_index, None)

    #####################################################################
    def getid_by_cucp_index(self, cucp_src: str, cucp_index: int) -> int:
        cucp_index = UniqueIndex(cucp_src, cucp_index)
        return self.contexts_by_cucp_index.get(cucp_index, None)

    #####################################################################
    def getid_by_cuup_index(self, cuup_src: str, cuup_index: int) -> int:
        cuup_index = UniqueIndex(cuup_src, cuup_index)
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
    def getid_by_cuup_ue_e1ap_id(self, cuup_src: str, cuup_ue_e1ap_id: int) -> int:
        cuup_ue_e1ap_id = (cuup_src, cuup_ue_e1ap_id)
        return self.contexts_by_cuup_ue_e1ap_id.get(cuup_ue_e1ap_id, None)

    #####################################################################
    def getid_by_ngap_ran_ue_id(self, cucp_src: str, ngap_ran_ue_id: int) -> int:

        if ngap_ran_ue_id is None:
            return None
        
        # filter contexts by ngap_ids.ran_ue_ngap_id
        filtered_contexts = {
            k: v for k, v in self.contexts.items()
            if v.ngap_ids is not None and v.ngap_ids.ran_ue_ngap_id == ngap_ran_ue_id
        }

        # filter where cucp_index.src matches cucp_src
        filtered_contexts = {
            k: v for k, v in filtered_contexts.items()
            if v.cucp_index is not None and v.cucp_index.src == cucp_src
        }

        if len(filtered_contexts) == 0:
            return None
        else:
            return list(filtered_contexts.keys())[0]

    #####################################################################
    def getid_by_ngap_amf_ue_id(self, cucp_src: str, ngap_amf_ue_id: int) -> int:

        if ngap_amf_ue_id is None:
            return None
        
        # filter contexts by ngap_ids.amf_ue_ngap_id
        filtered_contexts = {
            k: v for k, v in self.contexts.items()
            if v.ngap_ids is not None and v.ngap_ids.amf_ue_ngap_id == ngap_amf_ue_id
        }

        # filter where cucp_index.src matches cucp_src
        filtered_contexts = {
            k: v for k, v in filtered_contexts.items()
            if v.cucp_index is not None and v.cucp_index.src == cucp_src
        }


        if len(filtered_contexts) == 0:
            return None
        else:
            return list(filtered_contexts.keys())[0]

    #####################################################################
    def getid_by_ngap_ue_ids(self, ngap_ran_ue_id: int, ngap_amf_ue_id: int) -> int:

        if ngap_amf_ue_id is None and ngap_ran_ue_id is None:
            return None
        
        # filter contexts by ngap_ids.amf_ue_ngap_id
        filtered_contexts = {
            k: v for k, v in self.contexts.items()
            if v.ngap_ids == RanNgapUeIds(ngap_ran_ue_id, ngap_amf_ue_id)
        }

        if len(filtered_contexts) == 0:
            return None
        else:
            return list(filtered_contexts.keys())[0]

    #####################################################################
    def getid_by_tmsi(self, tmsi: int) -> int:

        if tmsi is None:
            return None
        
        # filter contexts by ngap_ids.amf_ue_ngap_id
        filtered_contexts = {
            k: v for k, v in self.contexts.items()
            if v.tmsi == tmsi
        }

        if len(filtered_contexts) == 0:
            return None
        else:
            return list(filtered_contexts.keys())[0]

    #####################################################################
    def get_amfid_by_ngap_ids(self, ngap_ids: RanNgapUeIds = None) -> int:

        if ngap_ids is None:
            return None

        # filter contexts by ngap_ids.ran_ue_ngap_id and ngap_ids.amf_ue_ngap_id
        filtered_contexts = {
            k: v for k, v in self.amf_contexts.items()
            if v[1].ngap_ids is not None and v[1].ngap_ids == ngap_ids
        }
        if len(filtered_contexts) > 0:
            amf_id = list(filtered_contexts.keys())[0]
            return amf_id

        return None

    #####################################################################
    def get_amfid_by_tmsi(self, tmsi: int = None) -> int:

        if tmsi is None:
            return None

         # Try current GUTI

        # filter contexts by current_guti.mtmsi
        filtered_contexts = {
            k: v for k, v in self.amf_contexts.items()
            if v[1].current_guti is not None and v[1].current_guti.mtmsi == tmsi
        }

        if len(filtered_contexts) > 0:
            amf_id = list(filtered_contexts.keys())[0]
            return amf_id

        # Try next GUTI

        # filter contexts by next_guti.mtmsi
        filtered_contexts = {
            k: v for k, v in self.amf_contexts.items()
            if v[1].next_guti is not None and v[1].next_guti.mtmsi == tmsi
        }

        if len(filtered_contexts) > 0:
            amf_id = list(filtered_contexts.keys())[0]
            return amf_id

        return None

    #####################################################################
    def get_amfid_by_core_amf_info(self, suci: str = None, supi: str = None, 
                               current_guti_plmn: str = None, current_guti_amf_id: str = None, current_guti_m_tmsi: int = None,
                               next_guti_plmn: str = None, next_guti_amf_id: str = None, next_guti_m_tmsi: int = None) -> int:

        # get UE by any of the unique identifying parameters
        amf_id = None
        if suci is not None:
            filtered_contexts = {
                k: v for k, v in self.amf_contexts.items()
                if v[1].suci is not None and v[1].suci == suci
            }
            if len(filtered_contexts) > 0:
                amf_id = list(filtered_contexts.keys())[0]
        elif amf_id is None and supi is not None:
            filtered_contexts = {
                k: v for k, v in self.amf_contexts.items()
                if v[1].supi is not None and v[1].supi == supi
            }
            if len(filtered_contexts) > 0:
                amf_id = list(filtered_contexts.keys())[0]
        elif amf_id is None and current_guti_plmn is not None:
            filtered_contexts = {
                k: v for k, v in self.amf_contexts.items()
                if v[1].current_guti is not None and \
                   v[1].current_guti.plmn_id == current_guti_plmn and \
                   v[1].current_guti.amf_id == current_guti_amf_id and \
                   v[1].current_guti.mtmsi == current_guti_m_tmsi
            }
            if len(filtered_contexts) > 0:
                amf_id = list(filtered_contexts.keys())[0]
        elif amf_id is None and next_guti_plmn is not None:
            filtered_contexts = {
                k: v for k, v in self.amf_contexts.items()
                if v[1].next_guti is not None and \
                   v[1].next_guti.plmn_id == next_guti_plmn and \
                   v[1].next_guti.amf_id == next_guti_amf_id and \
                   v[1].next_guti.mtmsi == next_guti_m_tmsi
            }
            if len(filtered_contexts) > 0:
                amf_id = list(filtered_contexts.keys())[0]
        else:
            # not found
            return None
        
        return amf_id

    #####################################################################
    def getid_by_core_amf_info(self, suci: str = None, supi: str = None, 
                               current_guti_plmn: str = None, current_guti_amf_id: str = None, current_guti_m_tmsi: int = None,
                               next_guti_plmn: str = None, next_guti_amf_id: str = None, next_guti_m_tmsi: int = None) -> int:

        # get amf context
        amf_id = self.get_amfid_by_core_amf_info(suci, supi, 
                               current_guti_plmn, current_guti_amf_id, current_guti_m_tmsi,
                               next_guti_plmn, next_guti_amf_id, next_guti_m_tmsi)
        
        if amf_id is not None:
            # get the UE context associated with the AMF context
            return self.amf_contexts[amf_id][0]
        
        return None
    
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
    def hook_du_ue_ctx_creation(self, du_src: str, du_index: int, plmn: int, pci: int, crnti: int, tac: int, nci: int,  now: dt.datetime = None) -> None:
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
        
        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        # Check if the UE context with the du index already exists
        # It should not exist, do if it does, delete it
        ue_id = self.getid_by_du_index(du_src, du_index)
        if ue_id is not None:
            if self.dbg:
                print(f"Unexpected UE context with du_src {du_src} du_index {du_index} already exists.  Stale UE will be deleted")
            self.context_delete(ue_id)

        du_index = UniqueIndex(du_src, du_index)

        ran_unique_ue_id = RanUniqueUeId(plmn, pci, crnti)

        # Check if the UE context with the unique info already exists
        # It should not exist, do if it does, delete it
        ue_id = self.getid_by_ran_unique_ue_id(ran_unique_ue_id)
        if ue_id is not None:
            if self.dbg:
                print(f"Unexpected UE context with [ran_unique_ue_id={ran_unique_ue_id}] already exists.  Stale UE will be deleted")
            self.context_delete(ue_id)

        # Create a new UE context
        self.context_create(ran_unique_ue_id, du_index=du_index, nci=nci, tac=tac)

    ####################################################################
    def hook_du_ue_ctx_update_crnti(self, du_src: str, du_index: int, crnti: int, now: dt.datetime = None) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_du_ue_ctx_update_crnti: du_src {du_src} du_index {du_index} crnti {crnti}")

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        ue_id = self.getid_by_du_index(du_src, du_index)
        if ue_id is None:
            if self.dbg:
                print(f"UE for du_src {du_src} du_index {du_index} could not be found.")
            return
        self.contexts[ue_id].ran_unique_ue_id = replace(
            self.contexts[ue_id].ran_unique_ue_id,
            crnti=crnti)

    ####################################################################
    def hook_du_ue_ctx_deletion(self, du_src: str, du_index: int, now: dt.datetime = None) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_du_ue_ctx_deletion: du_src {du_src} du_index {du_index}")

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        ue_id = self.getid_by_du_index(du_src, du_index)
        if ue_id is not None:
            self.clear_du_index(ue_id)

    ####################################################################
    def hook_cucp_uemgr_ue_add(self, cucp_src: str, cucp_index: str, plmn: int, pci: int, crnti: int, now: dt.datetime = None) -> None:
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

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        # Check if a UE context with the cucp index already exists
        # It should not, so delete it if it does 
        ue_id = self.getid_by_cucp_index(cucp_src, cucp_index)
        if ue_id is not None:
            if self.dbg:
                print(f"Unexpected UE context with cucp_src {cucp_src} cucp_index {cucp_index} already exists.  Stale UE will be deleted")
            self.context_delete(ue_id)

        cucp_index = UniqueIndex(cucp_src, cucp_index)

        ran_unique_ue_id = RanUniqueUeId(plmn, pci, crnti)

        # Check if a UE context with the unique info already exists
        # If it does not 
        #    create a new one
        # If it does, 
        #   check if the cucp index is currently set.
        #   If it is, delete the UE and create a new one
        #   If it is not, just update the cucp index
        ue_id = self.getid_by_ran_unique_ue_id(ran_unique_ue_id)
        if ue_id is None:
            # Create a new UE context
            self.context_create(ran_unique_ue_id, cucp_index=cucp_index)
        else:
            if self.contexts[ue_id].cucp_index is not None:
                if self.dbg:
                    print(f"Unexpected UE context with [ran_unique_ue_id={ran_unique_ue_id}] already exists.  Stale UE will be deleted")
                self.context_delete(ue_id)
                # Create a new UE context
                self.context_create(ran_unique_ue_id, cucp_index=cucp_index)
            else:
                if self.dbg:
                    print(f"UE context with [ran_unique_ue_id={ran_unique_ue_id}] already exists.  Setting cucp index")
                self.set_cucp_index(ue_id, cucp_index)
                if self.dbg:
                    print(f"UE context updated: {self.contexts[ue_id]}")

    ####################################################################
    def hook_cucp_uemgr_ue_remove(self, cucp_src: str, cucp_index: int, now: dt.datetime = None) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_cucp_uemgr_ue_remove: cucp_src {cucp_src} cucp_index {cucp_index}")

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        ue_id = self.getid_by_cucp_index(cucp_src, cucp_index)
        if ue_id is not None:
            self.clear_cucp_index(ue_id)

    ####################################################################
    def hook_e1_cucp_bearer_context_setup(self, cucp_src: str, cucp_index: int, gnb_cucp_ue_e1ap_id: int, now: dt.datetime = None) -> None:
        """
        Handle the E1AP Bearer Context Setup for CU-CP.

        :param cucp_index: The index of the UE in the CU-CP subsystem.
        :param gnb_cu_cp_ue_e1ap_id: The E1AP ID for the CU-CP.
        """

        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_e1_cucp_bearer_context_setup, cucp_src={cucp_src} cucp_index={cucp_index} gnb_cucp_ue_e1ap_id={gnb_cucp_ue_e1ap_id}")

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

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
    def hook_e1_cuup_bearer_context_setup(self, cuup_src: str, cuup_index: int, gnb_cucp_ue_e1ap_id: int, gnb_cuup_ue_e1ap_id: int, success: bool, now: dt.datetime = None) -> None:
        """
        Handle the E1AP Bearer Context Setup for CU-UP.

        :param cuup_index: The index of the UE in the CU-UP subsystem.
        :param gnb_cu_cp_ue_e1ap_id: The E1AP ID for the CU-CP.
        :param gnb_cu_up_ue_e1ap_id: The E1AP ID for the CU-UP.
        """

        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_e1_cuup_bearer_context_setup success={success}, cuup_src={cuup_src} cuup_index={cuup_index}  gnb_cu_cp_ue_e1ap_id={gnb_cucp_ue_e1ap_id} gnb_cu_up_ue_e1ap_id={gnb_cuup_ue_e1ap_id}")

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        cuup_index = UniqueIndex(cuup_src, cuup_index)
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
            self.clear_cucp_ue_e1ap_id(ue_id, bearer[0])
            return

        # set the cuup_ue_e1ap_id
        self.set_cuup_ue_e1ap_id(ue_id, bearer[0], gnb_cuup_ue_e1ap_id_tup)
        # update the cuup index
        self.set_cuup_index(ue_id, cuup_index)

    #####################################################################
    def hook_e1_cuup_bearer_context_release(self, cuup_src: str, cuup_index: int, cucp_ue_e1ap_id: int, cuup_ue_e1ap_id: int, success: bool, now: dt.datetime = None) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_e1_cuup_bearer_context_release success {success} cuup_src {cuup_src} cuup_index {cuup_index} gnb_cucp_ue_e1ap_id={cucp_ue_e1ap_id} gnb_cuup_ue_e1ap_id={cuup_ue_e1ap_id}")

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        cuup_index = UniqueIndex(cuup_src, cuup_index)

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
    def add_tmsi(self, cucp_src: str, cucp_index: int, tmsi: int, now: dt.datetime = None) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"add_tmsi: cucp_src={cucp_src} cucp_index={cucp_index} tmsi={tmsi}")

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        ue_id = self.getid_by_cucp_index(cucp_src, cucp_index)
        if ue_id is None:
            if self.dbg:
                print(f"UE context with cucp_src {cucp_src} cucp_index {cucp_index} not found. !!")
            return
        self.contexts[ue_id].tmsi = tmsi
        self.associate_ue_context_with_amf_tmsi(ue_id)

    #####################################################################
    def hook_ngap_procedure_started(self, cucp_src: str, cucp_index: int, procedure: int, ngap_ran_ue_id, ngap_amf_ue_id: int = None, now: dt.datetime = None) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_ngap_procedure_started: cucp_src={cucp_src} cucp_index={cucp_index} ngap_ran_ue_id={ngap_ran_ue_id} ngap_amf_ue_id={ngap_amf_ue_id}")

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        # get by ran_ue_id
        # if a UE has this already, and it is a different index, delete it from that UE
        ue_id = self.getid_by_ngap_ran_ue_id(cucp_src, ngap_ran_ue_id)
        if ue_id is not None and self.contexts[ue_id].cucp_index != UniqueIndex(cucp_src, cucp_index):
            self.contexts[ue_id].ngap_ids = None
                
        # get by amf_ue_id
        # if a UE has this already, and it is a different index, delete it from that UE
        if ngap_amf_ue_id is not None:
            ue_id = self.getid_by_ngap_amf_ue_id(cucp_src, ngap_amf_ue_id)
            if ue_id is not None and self.contexts[ue_id].cucp_index != UniqueIndex(cucp_src, cucp_index):
                self.contexts[ue_id].ngap_ids = None

        ue_id = self.getid_by_cucp_index(cucp_src, cucp_index)
        if ue_id is None:
            if self.dbg:
                print(f"UE context with cucp_src {cucp_src} cucp_index {cucp_index} not found. !!")
            return
        self.contexts[ue_id].ngap_ids = RanNgapUeIds(ngap_ran_ue_id, ngap_amf_ue_id)

    #####################################################################
    def hook_ngap_procedure_completed(self, cucp_src: str, cucp_index: int, procedure: int, success: bool, ngap_ran_ue_id: int, ngap_amf_ue_id: int, now: dt.datetime = None) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_ngap_procedure_completed: cucp_src={cucp_src} cucp_index={cucp_index} success={success} ngap_ran_ue_id={ngap_ran_ue_id} ngap_amf_ue_id={ngap_amf_ue_id}")

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        # get by ran_ue_id
        # if a UE has this already, and it is a different index, delete it from that UE
        ue_id = self.getid_by_ngap_ran_ue_id(cucp_src, ngap_ran_ue_id)
        if ue_id is not None and self.contexts[ue_id].cucp_index != UniqueIndex(cucp_src, cucp_index):
            self.contexts[ue_id].ngap_ids = None
                
        # get by amf_ue_id
        # if a UE has this already, and it is a different index, delete it from that UE
        ue_id = self.getid_by_ngap_amf_ue_id(cucp_src, ngap_amf_ue_id)
        if ue_id is not None and self.contexts[ue_id].cucp_index != UniqueIndex(cucp_src, cucp_index):
            self.contexts[ue_id].ngap_ids = None

        ue_id = self.getid_by_cucp_index(cucp_src, cucp_index)
        if ue_id is None:
            if self.dbg:
                print(f"UE context with cucp_src {cucp_src} cucp_index {cucp_index} not found. !!")
            return
        
        if not success:

            # if the procedure was the context setup, clear the ngap_ids
            if procedure == JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP:
                self.contexts[ue_id].ngap_ids = None
            
        else:

            # the procedure was a release, clear the ngap_ids
            if procedure == JbpfNgapProcedure.NGAP_PROCEDURE_UE_CONTEXT_RELEASE:
                 self.contexts[ue_id].ngap_ids = None

            else:
                self.contexts[ue_id].ngap_ids = RanNgapUeIds(ngap_ran_ue_id, ngap_amf_ue_id)
                self.associate_ue_context_with_amf_ngap(ue_id)


    #####################################################################
    def hook_ngap_reset(self, cucp_src: str, ngap_ran_ue_id: int = None, ngap_amf_ue_id: int = None, now: dt.datetime = None) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_ngap_reset: cucp_src={cucp_src} cucp_index={cucp_index} ngap_ran_ue_id={ngap_ran_ue_id} ngap_amf_ue_id={ngap_amf_ue_id}")

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        if ngap_ran_ue_id is None and ngap_amf_ue_id is None:
            # reset all contexts for this cucp

            if self.dbg:
                print(f"Resetting ngap_ids for all UEs with cucp_src '{cucp_src}'")

            # get all contexts with this cucp_src
            for ue_id, context in self.contexts.items():
                if context.cucp_index is not None and context.cucp_index.src == cucp_src:
                    context.ngap_ids = None
            return
            
        # get by ran_ue_id
        ue_id = self.getid_by_ngap_ran_ue_id(cucp_src, ngap_ran_ue_id)
        if ue_id is not None:
            if self.dbg:
                print(f"Resetting ngap_ids for UE context with cucp_src '{cucp_src}' ngap_ran_ue_id {ngap_ran_ue_id}")
            self.contexts[ue_id].ngap_ids = None     
            return
    
        # get by amf_ue_id
        ue_id = self.getid_by_ngap_amf_ue_id(cucp_src, ngap_amf_ue_id)
        if ue_id is not None:
            if self.dbg:
                print(f"Resetting ngap_ids for UE context with cucp_src '{cucp_src}' ngap_amf_ue_id {ngap_amf_ue_id}")
            self.contexts[ue_id].ngap_ids = None     
            return


    #####################################################################
    def hook_core_amf_info(self, ran_ue_ngap_id: int = None, amf_ue_ngap_id: int = None,
                              suci: str = None, supi: str = None, home_plmn_id: str = None,
                              current_guti_plmn: str = None, current_guti_amf_id: str = None, current_guti_m_tmsi: int = None,
                              next_guti_plmn: str = None, next_guti_amf_id: str = None, next_guti_m_tmsi: int = None,
                              tai_plmn: str = None, tai_tac: str = None,
                              cgi_plmn: str = None, cgi_cellid: str = None,
                              now: dt.datetime = None) -> None:

        if self.dbg:
            print(f"hook_core_amf_info: ran_ue_ngap_id={ran_ue_ngap_id}, amf_ue_ngap_id={amf_ue_ngap_id}, "
                                f"suci={suci}, supi={supi}, home_plmn_id={home_plmn_id}, "
                                f"current_guti_plmn={current_guti_plmn}, current_guti_amf_id={current_guti_amf_id}, "
                                f"current_guti_m_tmsi={current_guti_m_tmsi}, "
                                f"next_guti_plmn={next_guti_plmn}, next_guti_amf_id={next_guti_amf_id}, "
                                f"next_guti_m_tmsi={next_guti_m_tmsi}, "
                                f"tai_plmn={tai_plmn}, tai_tac={tai_tac}, "
                                f"cgi_plmn={cgi_plmn}, cgi_cellid={cgi_cellid}")
            
        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        if suci is None and supi is None and home_plmn_id is None and \
           current_guti_plmn is None and current_guti_amf_id is None and current_guti_m_tmsi is None and \
           next_guti_plmn is None and next_guti_amf_id is None and next_guti_m_tmsi is None and \
           tai_plmn is None and tai_tac is None and \
           cgi_plmn is None and cgi_cellid is None:
            # No AMF info present
            return
        
        self.amf_context_create_update(ran_ue_ngap_id, amf_ue_ngap_id,
                suci, supi, home_plmn_id,
                current_guti_plmn, current_guti_amf_id, current_guti_m_tmsi,
                next_guti_plmn, next_guti_amf_id, next_guti_m_tmsi,
                tai_plmn, tai_tac,
                cgi_plmn, cgi_cellid)

    #####################################################################
    def hook_core_amf_info_remove_ran(self, suci: str = None, supi: str = None, home_plmn_id: str = None,
                              current_guti_plmn: str = None, current_guti_amf_id: str = None, current_guti_m_tmsi: int = None,
                              next_guti_plmn: str = None, next_guti_amf_id: str = None, next_guti_m_tmsi: int = None,
                              tai_plmn: str = None, tai_tac: str = None,
                              cgi_plmn: str = None, cgi_cellid: str = None,
                              now: dt.datetime = None) -> None:

        if self.dbg:
            print(f"hook_core_amf_info_remove_ran: suci={suci}, supi={supi}, home_plmn_id={home_plmn_id}, "
                                f"current_guti_plmn={current_guti_plmn}, current_guti_amf_id={current_guti_amf_id}, "
                                f"current_guti_m_tmsi={current_guti_m_tmsi}, "
                                f"next_guti_plmn={next_guti_plmn}, next_guti_amf_id={next_guti_amf_id}, "
                                f"next_guti_m_tmsi={next_guti_m_tmsi}, "
                                f"tai_plmn={tai_plmn}, tai_tac={tai_tac}, "
                                f"cgi_plmn={cgi_plmn}, cgi_cellid={cgi_cellid}")
            
        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        # get UE by any of the unique identifying parameters
        amf_context_id = self.get_amfid_by_core_amf_info(suci, supi, 
                               current_guti_plmn, current_guti_amf_id, current_guti_m_tmsi,
                               next_guti_plmn, next_guti_amf_id, next_guti_m_tmsi)

        if amf_context_id is None:
            return

        # get UE
        ueid = self.getid_by_core_amf_info(suci, supi, 
                               current_guti_plmn, current_guti_amf_id, current_guti_m_tmsi,
                               next_guti_plmn, next_guti_amf_id, next_guti_m_tmsi)
        ue = self.getue_by_id(ueid)
        if ue is None:
            return

        self.disassociate_amf_context_with_ue(ue)

    #####################################################################
    def process_timeout(self, now: dt.datetime = None) -> None:

        self.now = now if now is not None else dt.datetime.now(dt.UTC)

        # filter contexts by current_guti.mtmsi
        filtered_contexts = {
            k: v for k, v in self.amf_contexts.items()
            if (v[2] is not None) and ((v[2]+self.amf_tmsi_expiry_secs) <= self.now)
        }

        if len(filtered_contexts) > 0:
            for k in filtered_contexts.keys():
                self.amf_context_delete(k)

    ####################################################################
    def get_num_contexts(self) -> int:
        return len(self.contexts)

    ####################################################################
    def __str__(self):
        return (
            f"UeContextsMap(\n"
            f"  contexts={self.contexts},\n"
            f"  contexts_by_du_index={self.contexts_by_du_index},\n"
            f"  contexts_by_cucp_index={self.contexts_by_cucp_index},\n"
            f"  contexts_by_cuup_index={self.contexts_by_cuup_index},\n"
            f"  contexts_by_cucp_ue_e1ap_id={self.contexts_by_cucp_ue_e1ap_id},\n"
            f"  contexts_by_cuup_ue_e1ap_id={self.contexts_by_cuup_ue_e1ap_id},\n"
            f"  amf_contexts={self.amf_contexts},\n"
            f")"
        )


##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################
if __name__ == "__main__":

    dbg = False

    s = UeContextsMap(dbg=dbg)

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
    assert ue is not None and ue.du_index == UniqueIndex("du1", 0) \
        and ue.cucp_index is None and ue.cuup_index is None \
        and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=401, crnti=20000) and ue.nci==201 and ue.tac==12

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
    assert ue is not None and ue.du_index==UniqueIndex(du1_src,1) and ue.cucp_index is None and ue.cuup_index is None \
           and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=401, crnti=20000) and ue.nci==201 and ue.tac==12


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
    assert ue is not None and ue.du_index==UniqueIndex(du1_src,1) and ue.cucp_index is None and ue.cuup_index is None \
           and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=401, crnti=20000) and ue.nci==201 and ue.tac==12
    ue_id = s.getid_by_du_index(du1_src, 2) 
    assert ue_id == 3
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==UniqueIndex(du1_src,2) and ue.cucp_index is None and ue.cuup_index is None \
           and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=401, crnti=20001) and ue.nci==201 and ue.tac==12

    
    
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
    assert ue is not None and ue.du_index is None and ue.cucp_index==UniqueIndex(cucp1_src, 0) and ue.cuup_index is None \
           and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=499, crnti=20000) and ue.nci is None and ue.tac is None


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
    assert ue is not None and ue.du_index==UniqueIndex(du1_src,1) and ue.cucp_index==UniqueIndex(cucp1_src, 1) and ue.cuup_index is None \
           and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=401, crnti=20000) and ue.nci==201 and ue.tac==12


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
    assert ue is not None and ue.du_index is None and ue.cucp_index==UniqueIndex(cucp1_src, 1) and ue.cuup_index is None \
           and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=401, crnti=20000) and ue.nci is None and ue.tac is None \


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
    assert ue is not None and ue.du_index is None and ue.cucp_index==UniqueIndex(cucp1_src, 1) and ue.cuup_index is None \
           and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=401, crnti=20000) and ue.nci is None and ue.tac is None \
           and len(ue.e1_bearers)==1 and ue.e1_bearers[0][0]==(cucp1_src,2000) and ue.e1_bearers[0][1] is None
    
    
    print("############################################################################")
    print("# Call hook_e1_cucp_bearer_context_setup again.  Ths will delete the context")
    s.hook_e1_cucp_bearer_context_setup(cucp1_src, 
                                        1,    # cucp_index
                                        2000) # cucp_ue_e1ap_id
    assert s.get_num_contexts() == 3


    print("#############################################################################")
    print("# delete s and start fresh")
    s = UeContextsMap(dbg=dbg)


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
    assert ue is not None and ue.du_index==UniqueIndex(du1_src,0) and ue.cucp_index==UniqueIndex(cucp1_src, 1) and ue.cuup_index is None \
           and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20000) and ue.nci==201 and ue.tac==12 \
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
    assert ue is not None and ue.du_index==UniqueIndex(du1_src,0) and ue.cucp_index==UniqueIndex(cucp1_src, 1) and ue.cuup_index==UniqueIndex(cuup1_src,10) \
           and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20000) and ue.nci==201 and ue.tac==12 \
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
    s = UeContextsMap(dbg=dbg)


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
        assert ctx is not None and ctx.du_index==UniqueIndex(du1_src,du_off+ue) and ctx.cucp_index==UniqueIndex(cucp1_src, cucp_off+ue) and ctx.cuup_index==UniqueIndex(cuup1_src,cuup_off+ue) \
               and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=crnti_off+ue) and ctx.nci==201 and ctx.tac==12 \
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
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index==UniqueIndex(cucp1_src, cucp_off+ue) and ctx.cuup_index==UniqueIndex(cuup1_src,cuup_off+ue) \
            and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=crnti_off+ue) and ctx.nci==201 and ctx.tac==12 \
            and len(ctx.e1_bearers)==num_e1 and \
            all(ctx.e1_bearers[i][0]==(cucp1_src, cucp_e1Off+(ue*num_e1)+i) and ctx.e1_bearers[i][1]==(cuup1_src, cuup_e1Off+(ue*num_e1)+i) for i in range(0, num_e1))
    s.hook_cucp_uemgr_ue_remove(cucp1_src, cucp_off+ue)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index is None and ctx.cuup_index==UniqueIndex(cuup1_src,cuup_off+ue) \
            and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=crnti_off+ue) and ctx.nci==201 and ctx.tac==12 \
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
    assert ctx is not None and ctx.du_index==UniqueIndex(du1_src,du_off+ue) and ctx.cucp_index==UniqueIndex(cucp1_src, cucp_off+ue) and ctx.cuup_index is None \
        and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=crnti_off+ue) and ctx.nci==201 and ctx.tac==12 \
        and len(ctx.e1_bearers)==0 
    s.hook_cucp_uemgr_ue_remove(cucp1_src, cucp_off+ue)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==UniqueIndex(du1_src,du_off+ue) and ctx.cucp_index is None and ctx.cuup_index is None \
        and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=crnti_off+ue) and ctx.nci==201 and ctx.tac==12 \
        and len(ctx.e1_bearers)==0 
    s.hook_du_ue_ctx_deletion(du1_src, du_off+ue)
    ctx = s.getue_by_id(ue)
    assert ctx is None


    print("#############################################################################")
    print("# delete s and start fresh")
    s = UeContextsMap(dbg=dbg)


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
        {'du_index': {'src': 'du0', 'idx': 0}, 'cucp_index': {'src': 'cucp0', 'idx': 0}, 'cuup_index': {'src': 'cuup0', 'idx': 0}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 30000}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp0', 0), ('cuup0', 0)), (('cucp0', 1), ('cuup0', 1))]},
        {'du_index': {'src': 'du0', 'idx': 1}, 'cucp_index': {'src': 'cucp0', 'idx': 1}, 'cuup_index': {'src': 'cuup0', 'idx': 1}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 30001}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp0', 2), ('cuup0', 2)), (('cucp0', 3), ('cuup0', 3))]},
        {'du_index': {'src': 'du0', 'idx': 2}, 'cucp_index': {'src': 'cucp0', 'idx': 2}, 'cuup_index': {'src': 'cuup0', 'idx': 2}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 30002}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp0', 4), ('cuup0', 4)), (('cucp0', 5), ('cuup0', 5))]},
        {'du_index': {'src': 'du0', 'idx': 3}, 'cucp_index': {'src': 'cucp0', 'idx': 3}, 'cuup_index': {'src': 'cuup0', 'idx': 3}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 30003}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp0', 6), ('cuup0', 6)), (('cucp0', 7), ('cuup0', 7))]},
        {'du_index': {'src': 'du1', 'idx': 0}, 'cucp_index': {'src': 'cucp0', 'idx': 4}, 'cuup_index': {'src': 'cuup0', 'idx': 4}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 401, 'crnti': 30000}, 'nci': 202, 'tac': 13, 'e1_bearers': [(('cucp0', 8), ('cuup0', 8)), (('cucp0', 9), ('cuup0', 9))]},
        {'du_index': {'src': 'du1', 'idx': 1}, 'cucp_index': {'src': 'cucp0', 'idx': 5}, 'cuup_index': {'src': 'cuup0', 'idx': 5}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 401, 'crnti': 30001}, 'nci': 202, 'tac': 13, 'e1_bearers': [(('cucp0', 10), ('cuup0', 10)), (('cucp0', 11), ('cuup0', 11))]},
        {'du_index': {'src': 'du1', 'idx': 2}, 'cucp_index': {'src': 'cucp0', 'idx': 6}, 'cuup_index': {'src': 'cuup1', 'idx': 0}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 401, 'crnti': 30002}, 'nci': 202, 'tac': 13, 'e1_bearers': [(('cucp0', 12), ('cuup1', 0)), (('cucp0', 13), ('cuup1', 1))]},
        {'du_index': {'src': 'du1', 'idx': 3}, 'cucp_index': {'src': 'cucp0', 'idx': 7}, 'cuup_index': {'src': 'cuup1', 'idx': 1}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 401, 'crnti': 30003}, 'nci': 202, 'tac': 13, 'e1_bearers': [(('cucp0', 14), ('cuup1', 2)), (('cucp0', 15), ('cuup1', 3))]},
        {'du_index': {'src': 'du2', 'idx': 0}, 'cucp_index': {'src': 'cucp0', 'idx': 8}, 'cuup_index': {'src': 'cuup1', 'idx': 2}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 402, 'crnti': 30000}, 'nci': 203, 'tac': 14, 'e1_bearers': [(('cucp0', 16), ('cuup1', 4)), (('cucp0', 17), ('cuup1', 5))]},
        {'du_index': {'src': 'du2', 'idx': 1}, 'cucp_index': {'src': 'cucp0', 'idx': 9}, 'cuup_index': {'src': 'cuup1', 'idx': 3}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 402, 'crnti': 30001}, 'nci': 203, 'tac': 14, 'e1_bearers': [(('cucp0', 18), ('cuup1', 6)), (('cucp0', 19), ('cuup1', 7))]},
        {'du_index': {'src': 'du2', 'idx': 2}, 'cucp_index': {'src': 'cucp0', 'idx': 10}, 'cuup_index': {'src': 'cuup1', 'idx': 4}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 402, 'crnti': 30002}, 'nci': 203, 'tac': 14, 'e1_bearers': [(('cucp0', 20), ('cuup1', 8)), (('cucp0', 21), ('cuup1', 9))]},
        {'du_index': {'src': 'du2', 'idx': 3}, 'cucp_index': {'src': 'cucp0', 'idx': 11}, 'cuup_index': {'src': 'cuup1', 'idx': 5}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 402, 'crnti': 30003}, 'nci': 203, 'tac': 14, 'e1_bearers': [(('cucp0', 22), ('cuup1', 10)), (('cucp0', 23), ('cuup1', 11))]}]    
    expected_contexts_by_du_index = {'du0::0': 0, 'du0::1': 1, 'du0::2': 2, 'du0::3': 3, 'du1::0': 4, 'du1::1': 5, 'du1::2': 6, 'du1::3': 7, 'du2::0': 8, 'du2::1': 9, 'du2::2': 10, 'du2::3': 11}
    expected_contexts_by_cucp_index= {'cucp0::0': 0, 'cucp0::1': 1, 'cucp0::2': 2, 'cucp0::3': 3, 'cucp0::4': 4, 'cucp0::5': 5, 'cucp0::6': 6, 'cucp0::7': 7, 'cucp0::8': 8, 'cucp0::9': 9, 'cucp0::10': 10, 'cucp0::11': 11}
    expected_contexts_by_cuup_index= {'cuup0::0': 0, 'cuup0::1': 1, 'cuup0::2': 2, 'cuup0::3': 3, 'cuup0::4': 4, 'cuup0::5': 5, 'cuup1::0': 6, 'cuup1::1': 7, 'cuup1::2': 8, 'cuup1::3': 9, 'cuup1::4': 10, 'cuup1::5': 11}
    expected_contexts_by_cucp_ue_e1ap_id= {'cucp0::0': 0, 'cucp0::1': 0, 'cucp0::2': 1, 'cucp0::3': 1, 'cucp0::4': 2, 'cucp0::5': 2, 'cucp0::6': 3, 'cucp0::7': 3, 'cucp0::8': 4, 'cucp0::9': 4, 'cucp0::10': 5, 'cucp0::11': 5, 'cucp0::12': 6, 'cucp0::13': 6, 'cucp0::14': 7, 'cucp0::15': 7, 'cucp0::16': 8, 'cucp0::17': 8, 'cucp0::18': 9, 'cucp0::19': 9, 'cucp0::20': 10, 'cucp0::21': 10, 'cucp0::22': 11, 'cucp0::23': 11}
    expected_contexts_by_cuup_ue_e1ap_id= {'cuup0::0': 0, 'cuup0::1': 0, 'cuup0::2': 1, 'cuup0::3': 1, 'cuup0::4': 2, 'cuup0::5': 2, 'cuup0::6': 3, 'cuup0::7': 3, 'cuup0::8': 4, 'cuup0::9': 4, 'cuup0::10': 5, 'cuup0::11': 5, 'cuup1::0': 6, 'cuup1::1': 6, 'cuup1::2': 7, 'cuup1::3': 7, 'cuup1::4': 8, 'cuup1::5': 8, 'cuup1::6': 9, 'cuup1::7': 9, 'cuup1::8': 10, 'cuup1::9': 10, 'cuup1::10': 11, 'cuup1::11': 11}

    for i in range(0, num_ue):
        ctx = s.getue_by_id(i)
        assert ctx.concise_dict() == expected_contexts[i]

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
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index==UniqueIndex('cucp0', 11) and ctx.cuup_index==UniqueIndex('cuup1', 5) \
            and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=402, crnti=30003) and ctx.nci==203 and ctx.tac==14 \
            and len(ctx.e1_bearers)==2 \
            and ctx.e1_bearers[0][0]==('cucp0', 22) and ctx.e1_bearers[0][1]==('cuup1', 10) and ctx.e1_bearers[1][0]==('cucp0', 23) and ctx.e1_bearers[1][1]==('cuup1', 11)
    
    s.hook_cucp_uemgr_ue_remove('cucp0', 11)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index is None and ctx.cuup_index==UniqueIndex('cuup1', 5) \
            and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=402, crnti=30003) and ctx.nci==203 and ctx.tac==14 \
            and len(ctx.e1_bearers)==2 \
            and ctx.e1_bearers[0][0]==('cucp0', 22) and ctx.e1_bearers[0][1]==('cuup1', 10) and ctx.e1_bearers[1][0]==('cucp0', 23) and ctx.e1_bearers[1][1]==('cuup1', 11)
   
    # try an e1ap_ids=22/13.   e1ap_id=13 is not known so nothing should happen
    s.hook_e1_cuup_bearer_context_release('cuup1', 5, 22, 13, True)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index is None and ctx.cuup_index==UniqueIndex('cuup1', 5) \
            and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=402, crnti=30003) and ctx.nci==203 and ctx.tac==14 \
            and len(ctx.e1_bearers)==2 \
            and ctx.e1_bearers[0][0]==('cucp0', 22) and ctx.e1_bearers[0][1]==('cuup1', 10) and ctx.e1_bearers[1][0]==('cucp0', 23) and ctx.e1_bearers[1][1]==('cuup1', 11)

    # delete 22/10. 
    s.hook_e1_cuup_bearer_context_release('cuup1', 5, 22, 10, True)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index is None and ctx.cuup_index==UniqueIndex('cuup1', 5) \
            and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=402, crnti=30003) and ctx.nci==203 and ctx.tac==14 \
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
    assert ctx is not None and ctx.du_index==UniqueIndex('du1', 0) and ctx.cucp_index==UniqueIndex('cucp0', 4) and ctx.cuup_index==UniqueIndex('cuup0', 4) \
            and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=401, crnti=30000) and ctx.nci==202 and ctx.tac==13 \
            and len(ctx.e1_bearers)==1 \
            and ctx.e1_bearers[0][0]==('cucp0', 8) and ctx.e1_bearers[0][1]==('cuup0', 8)

    s.hook_e1_cuup_bearer_context_release('cuup0', 4, 8, 8, True)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==UniqueIndex('du1', 0) and ctx.cucp_index==UniqueIndex('cucp0', 4) and ctx.cuup_index is None \
            and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=401, crnti=30000) and ctx.nci==202 and ctx.tac==13 \
            and len(ctx.e1_bearers)==0
             
    s.hook_cucp_uemgr_ue_remove('cucp0', 4)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==UniqueIndex('du1', 0) and ctx.cucp_index is None and ctx.cuup_index is None \
            and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=401, crnti=30000) and ctx.nci==202 and ctx.tac==13 \
            and len(ctx.e1_bearers)==0

    s.hook_du_ue_ctx_deletion('du1', 0)
    ctx = s.getue_by_id(ue)
    assert ctx is None
    assert s.get_num_contexts() == 10      


    print("#############################################################################")
    print("# delete s and start fresh")
    s = UeContextsMap(dbg=dbg)


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
    assert ctx is not None and ctx.du_index==UniqueIndex(du_src, du_index) and ctx.cucp_index==UniqueIndex(cucp_src, cucp_index) and ctx.cuup_index==UniqueIndex(cuup_src, cuup_index) \
        and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=plmn, pci=pci, crnti=crnti) and ctx.nci==nci and ctx.tac==tac \
        and len(ctx.e1_bearers)==1 \
        and ctx.e1_bearers[0][0]==(cucp_src, cucp_ue_e1ap_id) and ctx.e1_bearers[0][1]==(cuup_src, cuup_ue_e1ap_id) 
    assert s.get_num_contexts() == 1

    s.hook_e1_cuup_bearer_context_release(cuup_src, cuup_index, cucp_ue_e1ap_id, cuup_ue_e1ap_id, True)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==UniqueIndex(du_src, du_index) and ctx.cucp_index==UniqueIndex(cucp_src, cucp_index) and ctx.cuup_index is None \
        and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=plmn, pci=pci, crnti=crnti) and ctx.nci==nci and ctx.tac==tac \
        and len(ctx.e1_bearers)==0
    assert s.get_num_contexts() == 1

    s.hook_du_ue_ctx_deletion(du_src, du_index)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index==UniqueIndex(cucp_src, cucp_index) and ctx.cuup_index is None \
        and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=plmn, pci=pci, crnti=crnti) and ctx.nci==nci and ctx.tac==tac \
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
    assert ctx is not None and ctx.du_index==UniqueIndex(du_src, du_index) and ctx.cucp_index==UniqueIndex(cucp_src, cucp_index) and ctx.cuup_index==UniqueIndex(cuup_src, cuup_index) \
        and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=plmn, pci=pci, crnti=crnti) and ctx.nci==nci and ctx.tac==tac \
        and len(ctx.e1_bearers)==1 \
        and ctx.e1_bearers[0][0]==(cucp_src, cucp_ue_e1ap_id) and ctx.e1_bearers[0][1]==(cuup_src, cuup_ue_e1ap_id) 
    assert s.get_num_contexts() == 1

    new_crnti = 40000

    # this one should fail as the du_index is unknown
    s.hook_du_ue_ctx_update_crnti(du_src, du_index+1, new_crnti)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==UniqueIndex(du_src, du_index) and ctx.cucp_index==UniqueIndex(cucp_src, cucp_index) and ctx.cuup_index==UniqueIndex(cuup_src, cuup_index) \
        and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=plmn, pci=pci, crnti=crnti) and ctx.nci==nci and ctx.tac==tac \
        and len(ctx.e1_bearers)==1 \
        and ctx.e1_bearers[0][0]==(cucp_src, cucp_ue_e1ap_id) and ctx.e1_bearers[0][1]==(cuup_src, cuup_ue_e1ap_id) 
    assert s.get_num_contexts() == 1

    # this one should change the crnti
    s.hook_du_ue_ctx_update_crnti(du_src, du_index, new_crnti)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==UniqueIndex(du_src, du_index) and ctx.cucp_index==UniqueIndex(cucp_src, cucp_index) and ctx.cuup_index==UniqueIndex(cuup_src, cuup_index) \
        and ctx.ran_unique_ue_id==RanUniqueUeId(plmn=plmn, pci=pci, crnti=new_crnti) and ctx.nci==nci and ctx.tac==tac \
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
    assert u.concise_dict() =={'du_index': {'src': 'du0', 'idx': 0}, 'cucp_index': {'src': 'cucp0', 'idx': 1}, 'cuup_index': {'src': 'cuup0', 'idx': 0}, 'ran_unique_ue_id': {'plmn': 61712, 'pci': 1, 'crnti': 40000}, 'nci': 6733824, 'tac': 1, 'e1_bearers': [(('cucp0', 1), ('cuup0', 1))], 'tmsi': 1234}
         
    print("#############################################################################")
    print("# Test NGAP Ids")
    s = UeContextsMap(dbg=dbg)

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
    
    assert s.get_num_contexts() == 10
    ue = s.getue_by_id(0)
    assert ue is not None and ue.du_index==UniqueIndex('du1', 100) and ue.cucp_index==UniqueIndex('cucp1', 200) and ue.cuup_index==UniqueIndex('cuup1', 300)\
        and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20000) and ue.nci==201 and ue.tac==12 \
        and len(ue.e1_bearers)==3 and ue.ngap_ids is None

    ###########################################
    # Set ue=0 with ran_ue_id only
    ue = s.getue_by_id(0)
    ue0_ngap_ran_ue_id = 4000
    s.hook_ngap_procedure_started( ue.cucp_index.src, ue.cucp_index.idx, JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                  ngap_ran_ue_id=ue0_ngap_ran_ue_id, ngap_amf_ue_id=None)
    assert s.get_num_contexts() == 10
    ue = s.getue_by_id(0)
    assert ue is not None and ue.du_index==UniqueIndex('du1', 100) and ue.cucp_index==UniqueIndex('cucp1', 200) and ue.cuup_index==UniqueIndex('cuup1', 300)\
        and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20000) and ue.nci==201 and ue.tac==12 \
        and len(ue.e1_bearers)==3 and ue.ngap_ids==RanNgapUeIds(ue0_ngap_ran_ue_id, None)

    # Set ue=1 with ran_ue_id only
    ue = s.getue_by_id(1)
    ue1_ngap_ran_ue_id = 4001
    s.hook_ngap_procedure_started( ue.cucp_index.src, ue.cucp_index.idx, JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                  ngap_ran_ue_id=ue1_ngap_ran_ue_id, ngap_amf_ue_id=None)
    ue = s.getue_by_id(1)
    assert ue is not None and ue.du_index==UniqueIndex('du1', 101) and ue.cucp_index==UniqueIndex('cucp1', 201) and ue.cuup_index==UniqueIndex('cuup1', 301)\
        and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20001) and ue.nci==201 and ue.tac==12 \
        and len(ue.e1_bearers)==3 and ue.ngap_ids==RanNgapUeIds(ue1_ngap_ran_ue_id, None)

    # Set ue=0 with ran_ue_id of ue1
    ue = s.getue_by_id(0)
    s.hook_ngap_procedure_started( ue.cucp_index.src, ue.cucp_index.idx, JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                  ngap_ran_ue_id=ue1_ngap_ran_ue_id, ngap_amf_ue_id=None)
    assert s.get_num_contexts() == 10
    ue = s.getue_by_id(0)
    assert ue is not None and ue.du_index==UniqueIndex('du1', 100) and ue.cucp_index==UniqueIndex('cucp1', 200) and ue.cuup_index==UniqueIndex('cuup1', 300)\
        and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20000) and ue.nci==201 and ue.tac==12 \
        and len(ue.e1_bearers)==3 and ue.ngap_ids==RanNgapUeIds(ue1_ngap_ran_ue_id, None)
    ue = s.getue_by_id(1)
    assert ue is not None and ue.du_index==UniqueIndex('du1', 101) and ue.cucp_index==UniqueIndex('cucp1', 201) and ue.cuup_index==UniqueIndex('cuup1', 301)\
        and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20001) and ue.nci==201 and ue.tac==12 \
        and len(ue.e1_bearers)==3 and ue.ngap_ids is None
    


    # Set ue=0 with amf_ue_id 
    ue = s.getue_by_id(0)
    ue0_ngap_amf_ue_id = 14000
    s.hook_ngap_procedure_started( ue.cucp_index.src, ue.cucp_index.idx, JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                  ngap_ran_ue_id=1, ngap_amf_ue_id=ue0_ngap_amf_ue_id)
    assert s.get_num_contexts() == 10
    ue = s.getue_by_id(0)
    assert ue is not None and ue.du_index==UniqueIndex('du1', 100) and ue.cucp_index==UniqueIndex('cucp1', 200) and ue.cuup_index==UniqueIndex('cuup1', 300)\
        and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20000) and ue.nci==201 and ue.tac==12 \
        and len(ue.e1_bearers)==3 and ue.ngap_ids==RanNgapUeIds(1, ue0_ngap_amf_ue_id)

    # Set ue=1 with amf_ue_id
    ue = s.getue_by_id(1)
    ue1_ngap_amf_ue_id = 14001
    s.hook_ngap_procedure_started( ue.cucp_index.src, ue.cucp_index.idx, JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                  ngap_ran_ue_id=2, ngap_amf_ue_id=ue1_ngap_amf_ue_id)
    ue = s.getue_by_id(1)
    assert ue is not None and ue.du_index==UniqueIndex('du1', 101) and ue.cucp_index==UniqueIndex('cucp1', 201) and ue.cuup_index==UniqueIndex('cuup1', 301)\
        and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20001) and ue.nci==201 and ue.tac==12 \
        and len(ue.e1_bearers)==3 and ue.ngap_ids==RanNgapUeIds(2, ue1_ngap_amf_ue_id)

    # Set ue=0 with amf_ue_id of ue1
    ue = s.getue_by_id(0)
    s.hook_ngap_procedure_started( ue.cucp_index.src, ue.cucp_index.idx, JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                  ngap_ran_ue_id=2, ngap_amf_ue_id=ue1_ngap_amf_ue_id)
    assert s.get_num_contexts() == 10
    ue = s.getue_by_id(0)
    assert ue is not None and ue.du_index==UniqueIndex('du1', 100) and ue.cucp_index==UniqueIndex('cucp1', 200) and ue.cuup_index==UniqueIndex('cuup1', 300)\
        and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20000) and ue.nci==201 and ue.tac==12 \
        and len(ue.e1_bearers)==3 and ue.ngap_ids==RanNgapUeIds(2, ue1_ngap_amf_ue_id)
    ue = s.getue_by_id(1)
    assert ue is not None and ue.du_index==UniqueIndex('du1', 101) and ue.cucp_index==UniqueIndex('cucp1', 201) and ue.cuup_index==UniqueIndex('cuup1', 301)\
        and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20001) and ue.nci==201 and ue.tac==12 \
        and len(ue.e1_bearers)==3 and ue.ngap_ids is None

    ######################################################
    # try setting to an unknown cucp/cupp index
    s.hook_ngap_procedure_started( 'cucp1', 900, JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                  ngap_ran_ue_id=800, ngap_amf_ue_id=800)
    assert s.get_num_contexts() == 10

    ###########################################
    #  set all UES with ngap Ids


    # Set ue=0 with ran_ue_id only
    ue = s.getue_by_id(0)
    ue0_ngap_ran_ue_id = 4000
    s.hook_ngap_procedure_started( ue.cucp_index.src, ue.cucp_index.idx, JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                  ngap_ran_ue_id=ue0_ngap_ran_ue_id, ngap_amf_ue_id=None)
    assert s.get_num_contexts() == 10
    ue = s.getue_by_id(0)
    assert ue is not None and ue.du_index==UniqueIndex('du1', 100) and ue.cucp_index==UniqueIndex('cucp1', 200) and ue.cuup_index==UniqueIndex('cuup1', 300)\
        and ue.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20000) and ue.nci==201 and ue.tac==12 \
        and len(ue.e1_bearers)==3 and ue.ngap_ids==RanNgapUeIds(ue0_ngap_ran_ue_id, None)


    num_ue = 10
    cucp_off = 200
    ngap_ran_ue_id_off = 4000
    ngap_amf_ue_id_off = 14000

    for ue in range(0, num_ue):
        # create cucp context
        s.hook_ngap_procedure_started(  cucp1_src, 
                                        cucp_off+ue,
                                        JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                        ngap_ran_ue_id=ngap_ran_ue_id_off+ue, 
                                        ngap_amf_ue_id=None)
    # assert the expected contexts
    expected_contexts = [
        {'du_index': {'src': 'du1', 'idx': 100}, 'cucp_index': {'src': 'cucp1', 'idx': 200}, 'cuup_index': {'src': 'cuup1', 'idx': 300}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20000}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20000), ('cuup1', 30000)), (('cucp1', 20001), ('cuup1', 30001)), (('cucp1', 20002), ('cuup1', 30002))], 'ngap_ids': {'ran_ue_ngap_id': 4000, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 101}, 'cucp_index': {'src': 'cucp1', 'idx': 201}, 'cuup_index': {'src': 'cuup1', 'idx': 301}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20001}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20003), ('cuup1', 30003)), (('cucp1', 20004), ('cuup1', 30004)), (('cucp1', 20005), ('cuup1', 30005))], 'ngap_ids': {'ran_ue_ngap_id': 4001, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 102}, 'cucp_index': {'src': 'cucp1', 'idx': 202}, 'cuup_index': {'src': 'cuup1', 'idx': 302}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20002}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20006), ('cuup1', 30006)), (('cucp1', 20007), ('cuup1', 30007)), (('cucp1', 20008), ('cuup1', 30008))], 'ngap_ids': {'ran_ue_ngap_id': 4002, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 103}, 'cucp_index': {'src': 'cucp1', 'idx': 203}, 'cuup_index': {'src': 'cuup1', 'idx': 303}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20003}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20009), ('cuup1', 30009)), (('cucp1', 20010), ('cuup1', 30010)), (('cucp1', 20011), ('cuup1', 30011))], 'ngap_ids': {'ran_ue_ngap_id': 4003, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 104}, 'cucp_index': {'src': 'cucp1', 'idx': 204}, 'cuup_index': {'src': 'cuup1', 'idx': 304}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20004}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20012), ('cuup1', 30012)), (('cucp1', 20013), ('cuup1', 30013)), (('cucp1', 20014), ('cuup1', 30014))], 'ngap_ids': {'ran_ue_ngap_id': 4004, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 105}, 'cucp_index': {'src': 'cucp1', 'idx': 205}, 'cuup_index': {'src': 'cuup1', 'idx': 305}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20005}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20015), ('cuup1', 30015)), (('cucp1', 20016), ('cuup1', 30016)), (('cucp1', 20017), ('cuup1', 30017))], 'ngap_ids': {'ran_ue_ngap_id': 4005, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 106}, 'cucp_index': {'src': 'cucp1', 'idx': 206}, 'cuup_index': {'src': 'cuup1', 'idx': 306}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20006}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20018), ('cuup1', 30018)), (('cucp1', 20019), ('cuup1', 30019)), (('cucp1', 20020), ('cuup1', 30020))], 'ngap_ids': {'ran_ue_ngap_id': 4006, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 107}, 'cucp_index': {'src': 'cucp1', 'idx': 207}, 'cuup_index': {'src': 'cuup1', 'idx': 307}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20007}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20021), ('cuup1', 30021)), (('cucp1', 20022), ('cuup1', 30022)), (('cucp1', 20023), ('cuup1', 30023))], 'ngap_ids': {'ran_ue_ngap_id': 4007, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 108}, 'cucp_index': {'src': 'cucp1', 'idx': 208}, 'cuup_index': {'src': 'cuup1', 'idx': 308}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20008}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20024), ('cuup1', 30024)), (('cucp1', 20025), ('cuup1', 30025)), (('cucp1', 20026), ('cuup1', 30026))], 'ngap_ids': {'ran_ue_ngap_id': 4008, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 109}, 'cucp_index': {'src': 'cucp1', 'idx': 209}, 'cuup_index': {'src': 'cuup1', 'idx': 309}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20009}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20027), ('cuup1', 30027)), (('cucp1', 20028), ('cuup1', 30028)), (('cucp1', 20029), ('cuup1', 30029))], 'ngap_ids': {'ran_ue_ngap_id': 4009, 'amf_ue_ngap_id': None}},
    ]

    for ue in range(0, num_ue):
        ctx = s.getue_by_id(ue)
        assert ctx.concise_dict() == expected_contexts[ue]

    for ue in range(0, num_ue):
        assert s.getid_by_ngap_ue_ids(ngap_ran_ue_id_off+ue, None) == ue

    
    ###########################################################################
    # Handle case where procedure completes with success = False
    for ue in range(0, 5):
        s.hook_ngap_procedure_completed( cucp1_src, 
                                         cucp_off+ue,
                                         JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                         False,  # success
                                         ngap_ran_ue_id=ngap_ran_ue_id_off+ue, 
                                         ngap_amf_ue_id=ngap_amf_ue_id_off+ue)
    expected_contexts = [
        {'du_index': {'src': 'du1', 'idx': 100}, 'cucp_index': {'src': 'cucp1', 'idx': 200}, 'cuup_index': {'src': 'cuup1', 'idx': 300}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20000}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20000), ('cuup1', 30000)), (('cucp1', 20001), ('cuup1', 30001)), (('cucp1', 20002), ('cuup1', 30002))]},
        {'du_index': {'src': 'du1', 'idx': 101}, 'cucp_index': {'src': 'cucp1', 'idx': 201}, 'cuup_index': {'src': 'cuup1', 'idx': 301}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20001}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20003), ('cuup1', 30003)), (('cucp1', 20004), ('cuup1', 30004)), (('cucp1', 20005), ('cuup1', 30005))]},
        {'du_index': {'src': 'du1', 'idx': 102}, 'cucp_index': {'src': 'cucp1', 'idx': 202}, 'cuup_index': {'src': 'cuup1', 'idx': 302}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20002}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20006), ('cuup1', 30006)), (('cucp1', 20007), ('cuup1', 30007)), (('cucp1', 20008), ('cuup1', 30008))]},
        {'du_index': {'src': 'du1', 'idx': 103}, 'cucp_index': {'src': 'cucp1', 'idx': 203}, 'cuup_index': {'src': 'cuup1', 'idx': 303}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20003}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20009), ('cuup1', 30009)), (('cucp1', 20010), ('cuup1', 30010)), (('cucp1', 20011), ('cuup1', 30011))]},
        {'du_index': {'src': 'du1', 'idx': 104}, 'cucp_index': {'src': 'cucp1', 'idx': 204}, 'cuup_index': {'src': 'cuup1', 'idx': 304}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20004}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20012), ('cuup1', 30012)), (('cucp1', 20013), ('cuup1', 30013)), (('cucp1', 20014), ('cuup1', 30014))]},
        {'du_index': {'src': 'du1', 'idx': 105}, 'cucp_index': {'src': 'cucp1', 'idx': 205}, 'cuup_index': {'src': 'cuup1', 'idx': 305}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20005}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20015), ('cuup1', 30015)), (('cucp1', 20016), ('cuup1', 30016)), (('cucp1', 20017), ('cuup1', 30017))], 'ngap_ids': {'ran_ue_ngap_id': 4005, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 106}, 'cucp_index': {'src': 'cucp1', 'idx': 206}, 'cuup_index': {'src': 'cuup1', 'idx': 306}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20006}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20018), ('cuup1', 30018)), (('cucp1', 20019), ('cuup1', 30019)), (('cucp1', 20020), ('cuup1', 30020))], 'ngap_ids': {'ran_ue_ngap_id': 4006, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 107}, 'cucp_index': {'src': 'cucp1', 'idx': 207}, 'cuup_index': {'src': 'cuup1', 'idx': 307}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20007}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20021), ('cuup1', 30021)), (('cucp1', 20022), ('cuup1', 30022)), (('cucp1', 20023), ('cuup1', 30023))], 'ngap_ids': {'ran_ue_ngap_id': 4007, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 108}, 'cucp_index': {'src': 'cucp1', 'idx': 208}, 'cuup_index': {'src': 'cuup1', 'idx': 308}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20008}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20024), ('cuup1', 30024)), (('cucp1', 20025), ('cuup1', 30025)), (('cucp1', 20026), ('cuup1', 30026))], 'ngap_ids': {'ran_ue_ngap_id': 4008, 'amf_ue_ngap_id': None}},
        {'du_index': {'src': 'du1', 'idx': 109}, 'cucp_index': {'src': 'cucp1', 'idx': 209}, 'cuup_index': {'src': 'cuup1', 'idx': 309}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20009}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20027), ('cuup1', 30027)), (('cucp1', 20028), ('cuup1', 30028)), (('cucp1', 20029), ('cuup1', 30029))], 'ngap_ids': {'ran_ue_ngap_id': 4009, 'amf_ue_ngap_id': None}},
    ]
    for ue in range(0, num_ue):
        ctx = s.getue_by_id(ue)
        assert ctx.concise_dict() == expected_contexts[ue]

    ###########################################################################
    # Handle case where procedure completes with success = Success
    for ue in range(5, 10):
        s.hook_ngap_procedure_completed( cucp1_src, 
                                         cucp_off+ue,
                                         JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                         True,  # success
                                         ngap_ran_ue_id=ngap_ran_ue_id_off+ue, 
                                         ngap_amf_ue_id=ngap_amf_ue_id_off+ue)
    expected_contexts = [
        {'du_index': {'src': 'du1', 'idx': 100}, 'cucp_index': {'src': 'cucp1', 'idx': 200}, 'cuup_index': {'src': 'cuup1', 'idx': 300}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20000}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20000), ('cuup1', 30000)), (('cucp1', 20001), ('cuup1', 30001)), (('cucp1', 20002), ('cuup1', 30002))]},
        {'du_index': {'src': 'du1', 'idx': 101}, 'cucp_index': {'src': 'cucp1', 'idx': 201}, 'cuup_index': {'src': 'cuup1', 'idx': 301}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20001}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20003), ('cuup1', 30003)), (('cucp1', 20004), ('cuup1', 30004)), (('cucp1', 20005), ('cuup1', 30005))]},
        {'du_index': {'src': 'du1', 'idx': 102}, 'cucp_index': {'src': 'cucp1', 'idx': 202}, 'cuup_index': {'src': 'cuup1', 'idx': 302}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20002}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20006), ('cuup1', 30006)), (('cucp1', 20007), ('cuup1', 30007)), (('cucp1', 20008), ('cuup1', 30008))]},
        {'du_index': {'src': 'du1', 'idx': 103}, 'cucp_index': {'src': 'cucp1', 'idx': 203}, 'cuup_index': {'src': 'cuup1', 'idx': 303}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20003}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20009), ('cuup1', 30009)), (('cucp1', 20010), ('cuup1', 30010)), (('cucp1', 20011), ('cuup1', 30011))]},
        {'du_index': {'src': 'du1', 'idx': 104}, 'cucp_index': {'src': 'cucp1', 'idx': 204}, 'cuup_index': {'src': 'cuup1', 'idx': 304}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20004}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20012), ('cuup1', 30012)), (('cucp1', 20013), ('cuup1', 30013)), (('cucp1', 20014), ('cuup1', 30014))]},
        {'du_index': {'src': 'du1', 'idx': 105}, 'cucp_index': {'src': 'cucp1', 'idx': 205}, 'cuup_index': {'src': 'cuup1', 'idx': 305}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20005}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20015), ('cuup1', 30015)), (('cucp1', 20016), ('cuup1', 30016)), (('cucp1', 20017), ('cuup1', 30017))], 'ngap_ids': {'ran_ue_ngap_id': 4005, 'amf_ue_ngap_id': 14005}},
        {'du_index': {'src': 'du1', 'idx': 106}, 'cucp_index': {'src': 'cucp1', 'idx': 206}, 'cuup_index': {'src': 'cuup1', 'idx': 306}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20006}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20018), ('cuup1', 30018)), (('cucp1', 20019), ('cuup1', 30019)), (('cucp1', 20020), ('cuup1', 30020))], 'ngap_ids': {'ran_ue_ngap_id': 4006, 'amf_ue_ngap_id': 14006}},
        {'du_index': {'src': 'du1', 'idx': 107}, 'cucp_index': {'src': 'cucp1', 'idx': 207}, 'cuup_index': {'src': 'cuup1', 'idx': 307}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20007}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20021), ('cuup1', 30021)), (('cucp1', 20022), ('cuup1', 30022)), (('cucp1', 20023), ('cuup1', 30023))], 'ngap_ids': {'ran_ue_ngap_id': 4007, 'amf_ue_ngap_id': 14007}},
        {'du_index': {'src': 'du1', 'idx': 108}, 'cucp_index': {'src': 'cucp1', 'idx': 208}, 'cuup_index': {'src': 'cuup1', 'idx': 308}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20008}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20024), ('cuup1', 30024)), (('cucp1', 20025), ('cuup1', 30025)), (('cucp1', 20026), ('cuup1', 30026))], 'ngap_ids': {'ran_ue_ngap_id': 4008, 'amf_ue_ngap_id': 14008}},
        {'du_index': {'src': 'du1', 'idx': 109}, 'cucp_index': {'src': 'cucp1', 'idx': 209}, 'cuup_index': {'src': 'cuup1', 'idx': 309}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20009}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20027), ('cuup1', 30027)), (('cucp1', 20028), ('cuup1', 30028)), (('cucp1', 20029), ('cuup1', 30029))], 'ngap_ids': {'ran_ue_ngap_id': 4009, 'amf_ue_ngap_id': 14009}},
        ]    
    for ue in range(0, num_ue):
        ctx = s.getue_by_id(ue)
        assert ctx.concise_dict() == expected_contexts[ue]

    ###########################################################################
    # Handle RESET using ngap ran ue id
    ue = 6
    s.hook_ngap_reset( cucp1_src,
                       ngap_ran_ue_id=ngap_ran_ue_id_off+ue, 
                       ngap_amf_ue_id=None)
    uectx = s.getue_by_id(ue)
    assert uectx is not None and uectx.du_index==UniqueIndex('du1', 106) and uectx.cucp_index==UniqueIndex('cucp1', 206) and uectx.cuup_index==UniqueIndex('cuup1', 306)\
        and uectx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20006) and uectx.nci==201 and uectx.tac==12 \
        and len(uectx.e1_bearers)==3 and uectx.ngap_ids is None

    ###########################################################################
    # Handle RESET using ngap amf ue id
    ue = 7
    s.hook_ngap_reset( cucp1_src,
                       ngap_ran_ue_id=None, 
                       ngap_amf_ue_id=ngap_amf_ue_id_off+ue)
    uectx = s.getue_by_id(ue)
    assert uectx is not None and uectx.du_index==UniqueIndex('du1', 107) and uectx.cucp_index==UniqueIndex('cucp1', 207) and uectx.cuup_index==UniqueIndex('cuup1', 307)\
        and uectx.ran_unique_ue_id==RanUniqueUeId(plmn=101, pci=400, crnti=20007) and uectx.nci==201 and uectx.tac==12 \
        and len(uectx.e1_bearers)==3 and uectx.ngap_ids is None

    expected_contexts = [
        {'du_index': {'src': 'du1', 'idx': 100}, 'cucp_index': {'src': 'cucp1', 'idx': 200}, 'cuup_index': {'src': 'cuup1', 'idx': 300}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20000}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20000), ('cuup1', 30000)), (('cucp1', 20001), ('cuup1', 30001)), (('cucp1', 20002), ('cuup1', 30002))]},
        {'du_index': {'src': 'du1', 'idx': 101}, 'cucp_index': {'src': 'cucp1', 'idx': 201}, 'cuup_index': {'src': 'cuup1', 'idx': 301}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20001}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20003), ('cuup1', 30003)), (('cucp1', 20004), ('cuup1', 30004)), (('cucp1', 20005), ('cuup1', 30005))]},
        {'du_index': {'src': 'du1', 'idx': 102}, 'cucp_index': {'src': 'cucp1', 'idx': 202}, 'cuup_index': {'src': 'cuup1', 'idx': 302}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20002}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20006), ('cuup1', 30006)), (('cucp1', 20007), ('cuup1', 30007)), (('cucp1', 20008), ('cuup1', 30008))]},
        {'du_index': {'src': 'du1', 'idx': 103}, 'cucp_index': {'src': 'cucp1', 'idx': 203}, 'cuup_index': {'src': 'cuup1', 'idx': 303}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20003}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20009), ('cuup1', 30009)), (('cucp1', 20010), ('cuup1', 30010)), (('cucp1', 20011), ('cuup1', 30011))]},
        {'du_index': {'src': 'du1', 'idx': 104}, 'cucp_index': {'src': 'cucp1', 'idx': 204}, 'cuup_index': {'src': 'cuup1', 'idx': 304}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20004}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20012), ('cuup1', 30012)), (('cucp1', 20013), ('cuup1', 30013)), (('cucp1', 20014), ('cuup1', 30014))]},
        {'du_index': {'src': 'du1', 'idx': 105}, 'cucp_index': {'src': 'cucp1', 'idx': 205}, 'cuup_index': {'src': 'cuup1', 'idx': 305}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20005}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20015), ('cuup1', 30015)), (('cucp1', 20016), ('cuup1', 30016)), (('cucp1', 20017), ('cuup1', 30017))], 'ngap_ids': {'ran_ue_ngap_id': 4005, 'amf_ue_ngap_id': 14005}},
        {'du_index': {'src': 'du1', 'idx': 106}, 'cucp_index': {'src': 'cucp1', 'idx': 206}, 'cuup_index': {'src': 'cuup1', 'idx': 306}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20006}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20018), ('cuup1', 30018)), (('cucp1', 20019), ('cuup1', 30019)), (('cucp1', 20020), ('cuup1', 30020))]},
        {'du_index': {'src': 'du1', 'idx': 107}, 'cucp_index': {'src': 'cucp1', 'idx': 207}, 'cuup_index': {'src': 'cuup1', 'idx': 307}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20007}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20021), ('cuup1', 30021)), (('cucp1', 20022), ('cuup1', 30022)), (('cucp1', 20023), ('cuup1', 30023))]},
        {'du_index': {'src': 'du1', 'idx': 108}, 'cucp_index': {'src': 'cucp1', 'idx': 208}, 'cuup_index': {'src': 'cuup1', 'idx': 308}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20008}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20024), ('cuup1', 30024)), (('cucp1', 20025), ('cuup1', 30025)), (('cucp1', 20026), ('cuup1', 30026))], 'ngap_ids': {'ran_ue_ngap_id': 4008, 'amf_ue_ngap_id': 14008}},
        {'du_index': {'src': 'du1', 'idx': 109}, 'cucp_index': {'src': 'cucp1', 'idx': 209}, 'cuup_index': {'src': 'cuup1', 'idx': 309}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20009}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20027), ('cuup1', 30027)), (('cucp1', 20028), ('cuup1', 30028)), (('cucp1', 20029), ('cuup1', 30029))], 'ngap_ids': {'ran_ue_ngap_id': 4009, 'amf_ue_ngap_id': 14009}},
    ]
    for ue in range(0, num_ue):
        ctx = s.getue_by_id(ue)
        assert ctx.concise_dict() == expected_contexts[ue]

    ###########################################################################
    # Handle RESET of all contexts on a specific cucp src
    s.hook_ngap_reset( cucp1_src,
                       ngap_ran_ue_id=None, 
                       ngap_amf_ue_id=None)
    expected_contexts = [
        {'du_index': {'src': 'du1', 'idx': 100}, 'cucp_index': {'src': 'cucp1', 'idx': 200}, 'cuup_index': {'src': 'cuup1', 'idx': 300}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20000}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20000), ('cuup1', 30000)), (('cucp1', 20001), ('cuup1', 30001)), (('cucp1', 20002), ('cuup1', 30002))]},
        {'du_index': {'src': 'du1', 'idx': 101}, 'cucp_index': {'src': 'cucp1', 'idx': 201}, 'cuup_index': {'src': 'cuup1', 'idx': 301}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20001}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20003), ('cuup1', 30003)), (('cucp1', 20004), ('cuup1', 30004)), (('cucp1', 20005), ('cuup1', 30005))]},
        {'du_index': {'src': 'du1', 'idx': 102}, 'cucp_index': {'src': 'cucp1', 'idx': 202}, 'cuup_index': {'src': 'cuup1', 'idx': 302}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20002}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20006), ('cuup1', 30006)), (('cucp1', 20007), ('cuup1', 30007)), (('cucp1', 20008), ('cuup1', 30008))]},
        {'du_index': {'src': 'du1', 'idx': 103}, 'cucp_index': {'src': 'cucp1', 'idx': 203}, 'cuup_index': {'src': 'cuup1', 'idx': 303}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20003}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20009), ('cuup1', 30009)), (('cucp1', 20010), ('cuup1', 30010)), (('cucp1', 20011), ('cuup1', 30011))]},
        {'du_index': {'src': 'du1', 'idx': 104}, 'cucp_index': {'src': 'cucp1', 'idx': 204}, 'cuup_index': {'src': 'cuup1', 'idx': 304}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20004}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20012), ('cuup1', 30012)), (('cucp1', 20013), ('cuup1', 30013)), (('cucp1', 20014), ('cuup1', 30014))]},
        {'du_index': {'src': 'du1', 'idx': 105}, 'cucp_index': {'src': 'cucp1', 'idx': 205}, 'cuup_index': {'src': 'cuup1', 'idx': 305}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20005}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20015), ('cuup1', 30015)), (('cucp1', 20016), ('cuup1', 30016)), (('cucp1', 20017), ('cuup1', 30017))]},
        {'du_index': {'src': 'du1', 'idx': 106}, 'cucp_index': {'src': 'cucp1', 'idx': 206}, 'cuup_index': {'src': 'cuup1', 'idx': 306}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20006}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20018), ('cuup1', 30018)), (('cucp1', 20019), ('cuup1', 30019)), (('cucp1', 20020), ('cuup1', 30020))]},
        {'du_index': {'src': 'du1', 'idx': 107}, 'cucp_index': {'src': 'cucp1', 'idx': 207}, 'cuup_index': {'src': 'cuup1', 'idx': 307}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20007}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20021), ('cuup1', 30021)), (('cucp1', 20022), ('cuup1', 30022)), (('cucp1', 20023), ('cuup1', 30023))]},
        {'du_index': {'src': 'du1', 'idx': 108}, 'cucp_index': {'src': 'cucp1', 'idx': 208}, 'cuup_index': {'src': 'cuup1', 'idx': 308}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20008}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20024), ('cuup1', 30024)), (('cucp1', 20025), ('cuup1', 30025)), (('cucp1', 20026), ('cuup1', 30026))]},
        {'du_index': {'src': 'du1', 'idx': 109}, 'cucp_index': {'src': 'cucp1', 'idx': 209}, 'cuup_index': {'src': 'cuup1', 'idx': 309}, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20009}, 'nci': 201, 'tac': 12, 'e1_bearers': [(('cucp1', 20027), ('cuup1', 30027)), (('cucp1', 20028), ('cuup1', 30028)), (('cucp1', 20029), ('cuup1', 30029))]},
        ]
    for ue in range(0, num_ue):
        ctx = s.getue_by_id(ue)
        assert ctx.concise_dict() == expected_contexts[ue]

    print("#############################################################################")
    print("# Test Core info")
    s = UeContextsMap(dbg=dbg)

    plmn = 101
    pci =  400
    crnti = 20000
    du_src = 'du1'
    du_index = 100
    tac = 12
    nci = 201
    cucp_src = 'cucp1'
    cucp_index = 200
    ngap_ran_ue_id = 5000
    ngap_amf_ue_id = 15000

    s.hook_du_ue_ctx_creation(  du_src, 
                                du_index,
                                plmn,
                                pci,
                                crnti,
                                tac,
                                nci)
    s.hook_cucp_uemgr_ue_add(   cucp_src, 
                                cucp_index,
                                plmn,
                                pci,
                                crnti)
    s.hook_ngap_procedure_completed( cucp_src, 
                                     cucp_index,
                                     JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                     True,  # success
                                     ngap_ran_ue_id,
                                     ngap_amf_ue_id)    
    uectx = s.getue_by_id(0)
    assert uectx is not None and uectx.du_index==UniqueIndex(du_src, du_index) and uectx.cucp_index==UniqueIndex(cucp_src, cucp_index) and uectx.cuup_index is None \
        and uectx.ran_unique_ue_id==RanUniqueUeId(plmn=plmn, pci=pci, crnti=crnti) and uectx.nci==nci and uectx.tac==tac \
        and len(uectx.e1_bearers)==0 and uectx.ngap_ids==RanNgapUeIds(ngap_ran_ue_id, ngap_amf_ue_id)

    #################################### 
    ## Handle a failed setup
    s.hook_ngap_procedure_completed( cucp_src, 
                                     cucp_index,
                                     JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                     False,  # success
                                     ngap_ran_ue_id,
                                     ngap_amf_ue_id)    
    uectx = s.getue_by_id(0)
    assert uectx is not None and uectx.du_index==UniqueIndex(du_src, du_index) and uectx.cucp_index==UniqueIndex(cucp_src, cucp_index) and uectx.cuup_index is None \
        and uectx.ran_unique_ue_id==RanUniqueUeId(plmn=plmn, pci=pci, crnti=crnti) and uectx.nci==nci and uectx.tac==tac \
        and len(uectx.e1_bearers)==0 and uectx.ngap_ids is None

    #################################### 
    ## Handle a context release
    s.hook_ngap_procedure_completed( cucp_src, 
                                     cucp_index,
                                     JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                     True,  # success
                                     ngap_ran_ue_id,
                                     ngap_amf_ue_id)    
    uectx = s.getue_by_id(0)
    assert uectx is not None and uectx.du_index==UniqueIndex(du_src, du_index) and uectx.cucp_index==UniqueIndex(cucp_src, cucp_index) and uectx.cuup_index is None \
        and uectx.ran_unique_ue_id==RanUniqueUeId(plmn=plmn, pci=pci, crnti=crnti) and uectx.nci==nci and uectx.tac==tac \
        and len(uectx.e1_bearers)==0 and uectx.ngap_ids==RanNgapUeIds(ngap_ran_ue_id, ngap_amf_ue_id)
    s.hook_ngap_procedure_completed( cucp_src, 
                                     cucp_index,
                                     JbpfNgapProcedure.NGAP_PROCEDURE_UE_CONTEXT_RELEASE,
                                     True,  # success
                                     ngap_ran_ue_id,
                                     ngap_amf_ue_id)    
    uectx = s.getue_by_id(0)
    assert uectx is not None and uectx.du_index==UniqueIndex(du_src, du_index) and uectx.cucp_index==UniqueIndex(cucp_src, cucp_index) and uectx.cuup_index is None \
        and uectx.ran_unique_ue_id==RanUniqueUeId(plmn=plmn, pci=pci, crnti=crnti) and uectx.nci==nci and uectx.tac==tac \
        and len(uectx.e1_bearers)==0 and uectx.ngap_ids  is None

    ###############################################################
    # re-add context 
    s.hook_ngap_procedure_completed( cucp_src, 
                                     cucp_index,
                                     JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP,
                                     True,  # success
                                     ngap_ran_ue_id,
                                     ngap_amf_ue_id)    
    uectx = s.getue_by_id(0)
    assert uectx is not None and uectx.du_index==UniqueIndex(du_src, du_index) and uectx.cucp_index==UniqueIndex(cucp_src, cucp_index) and uectx.cuup_index is None \
        and uectx.ran_unique_ue_id==RanUniqueUeId(plmn=plmn, pci=pci, crnti=crnti) and uectx.nci==nci and uectx.tac==tac \
        and len(uectx.e1_bearers)==0 and uectx.ngap_ids==RanNgapUeIds(ngap_ran_ue_id, ngap_amf_ue_id)

    examples_with_no_ngap = [
        {},
        {"suci": "suci-0-001-01-0000-0-0-1230010004"}, 
        {"suci": "suci-0-001-01-0000-0-0-1230010004", "supi": "imsi-001011230010004", "home_plmn_id": "001F01"}, 
        {"suci": "suci-0-001-01-0000-0-0-1230010004", "supi": "imsi-001011230010004", "home_plmn_id": "001F01", 
         "current-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221226075 }}, 
        {"suci": "suci-0-001-01-0000-0-0-1230010004", "supi": "imsi-001011230010004", "home_plmn_id": "001F01", 
         "current-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221226075 }, 
         "next-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221225666 }},
        {"suci": "suci-0-001-01-0000-0-0-1230010004", "supi": "imsi-001011230010004", "home_plmn_id": "001F01", 
         "current-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221226075 }, 
         "next-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221225666 }, 
         "nr_tai": { "plmn_id": "00f110", "tac": "1" }},
        {"suci": "suci-0-001-01-0000-0-0-1230010004", "supi": "imsi-001011230010004", "home_plmn_id": "001F01", 
         "current-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221226075 }, 
         "next-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221225666 }, 
         "nr_tai": { "plmn_id": "00f110", "tac": "1" }, 
         "nr_cgi": { "plmn_id": "00f110", "cell_id": "66c000" }}]

    for idx,a in enumerate(examples_with_no_ngap):
        s.hook_core_amf_info(
            ran_ue_ngap_id=a.get("ran_ue", {}).get("ran_ue_ngap_id", None),
            amf_ue_ngap_id=a.get("ran_ue", {}).get("amf_ue_ngap_id", None),
            suci=a.get("suci", None),
            supi=a.get("supi", None),
            home_plmn_id=a.get("home_plmn_id", None),
            current_guti_plmn=a.get("current-guti", {}).get("plmn_id", None),
            current_guti_amf_id=a.get("current-guti", {}).get("amf_id", None),
            current_guti_m_tmsi=a.get("current-guti", {}).get("m_tmsi", None),
            next_guti_plmn=a.get("next-guti", {}).get("plmn_id", None),
            next_guti_amf_id=a.get("next-guti", {}).get("amf_id", None),
            next_guti_m_tmsi=a.get("next-guti", {}).get("m_tmsi", None),
            tai_plmn=a.get("nr_tai", {}).get("plmn_id", None),
            tai_tac=a.get("nr_tai", {}).get("tac", None),
            cgi_plmn=a.get("nr_cgi", {}).get("plmn_id", None),
            cgi_cellid=a.get("nr_cgi", {}).get("cell_id", None)
        )
        uectx = s.getue_by_id(0)
        assert uectx is not None and uectx.core_amf_info is None
    assert len(s.amf_contexts) == 1
        
    examples_with_mismatched_ngap = {
        "suci": "suci-0-001-01-0000-0-0-1230010004", "supi": "imsi-001011230010004", "home_plmn_id": "001F01", 
        "current-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221226075 }, 
        "next-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221225666 }, 
        "nr_tai": { "plmn_id": "00f110", "tac": "1" }, 
        "nr_cgi": { "plmn_id": "00f110", "cell_id": "66c000" }, 
        "ran_ue": {"ran_ue_id": 36, "ran_ue_ngap_id": 1234, "amf_ue_ngap_id": 4321}}
    a = examples_with_mismatched_ngap
    s.hook_core_amf_info(
        ran_ue_ngap_id=a.get("ran_ue", {}).get("ran_ue_ngap_id", None),
        amf_ue_ngap_id=a.get("ran_ue", {}).get("amf_ue_ngap_id", None),
        suci=a.get("suci", None),
        supi=a.get("supi", None),
        home_plmn_id=a.get("home_plmn_id", None),
        current_guti_plmn=a.get("current-guti", {}).get("plmn_id", None),
        current_guti_amf_id=a.get("current-guti", {}).get("amf_id", None),
        current_guti_m_tmsi=a.get("current-guti", {}).get("m_tmsi", None),
        next_guti_plmn=a.get("next-guti", {}).get("plmn_id", None),
        next_guti_amf_id=a.get("next-guti", {}).get("amf_id", None),
        next_guti_m_tmsi=a.get("next-guti", {}).get("m_tmsi", None),
        tai_plmn=a.get("nr_tai", {}).get("plmn_id", None),
        tai_tac=a.get("nr_tai", {}).get("tac", None),
        cgi_plmn=a.get("nr_cgi", {}).get("plmn_id", None),
        cgi_cellid=a.get("nr_cgi", {}).get("cell_id", None)
    )
    uectx = s.getue_by_id(0)
    assert uectx is not None and uectx.core_amf_info is None
    assert len(s.amf_contexts) == 1

    examples_with_matching_ngap = {
        "suci": "suci-0-001-01-0000-0-0-1230010004", "supi": "imsi-001011230010004", "home_plmn_id": "001F01", 
        "current-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221226075 }, 
        "next-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221225666 }, 
        "nr_tai": { "plmn_id": "00f110", "tac": "1" }, 
        "nr_cgi": { "plmn_id": "00f110", "cell_id": "66c000" }, 
        "ran_ue": {"ran_ue_id": 36, "ran_ue_ngap_id": ngap_ran_ue_id, "amf_ue_ngap_id": ngap_amf_ue_id}}
    a = examples_with_matching_ngap
    s.hook_core_amf_info(
        ran_ue_ngap_id=a.get("ran_ue", {}).get("ran_ue_ngap_id", None),
        amf_ue_ngap_id=a.get("ran_ue", {}).get("amf_ue_ngap_id", None),
        suci=a.get("suci", None),
        supi=a.get("supi", None),
        home_plmn_id=a.get("home_plmn_id", None),
        current_guti_plmn=a.get("current-guti", {}).get("plmn_id", None),
        current_guti_amf_id=a.get("current-guti", {}).get("amf_id", None),
        current_guti_m_tmsi=a.get("current-guti", {}).get("m_tmsi", None),
        next_guti_plmn=a.get("next-guti", {}).get("plmn_id", None),
        next_guti_amf_id=a.get("next-guti", {}).get("amf_id", None),
        next_guti_m_tmsi=a.get("next-guti", {}).get("m_tmsi", None),
        tai_plmn=a.get("nr_tai", {}).get("plmn_id", None),
        tai_tac=a.get("nr_tai", {}).get("tac", None),
        cgi_plmn=a.get("nr_cgi", {}).get("plmn_id", None),
        cgi_cellid=a.get("nr_cgi", {}).get("cell_id", None)
    )
    uectx = s.getue_by_id(0)
    assert uectx is not None and asdict(uectx) == {'du_index': {'src': 'du1', 'idx': 100}, 'cucp_index': {'src': 'cucp1', 'idx': 200}, 'cuup_index': None, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20000}, 'nci': 201, 'tac': 12, 'e1_bearers': [], 'tmsi': None, 'ngap_ids': {'ran_ue_ngap_id': 5000, 'amf_ue_ngap_id': 15000}, 'core_amf_context_index': 0, 'core_amf_info': {'suci': 'suci-0-001-01-0000-0-0-1230010004', 'supi': 'imsi-001011230010004', 'home_plmn_id': '001F01', 'current_guti': {'plmn_id': '999F99', 'amf_id': '20040', 'mtmsi': 3221226075}, 'next_guti': {'plmn_id': '999F99', 'amf_id': '20040', 'mtmsi': 3221225666}, 'tai': {'plmn_id': '00f110', 'tac': '1'}, 'cgi': {'plmn_id': '00f110', 'cell_id': '66c000'}, 'ngap_ids': {'ran_ue_ngap_id': 5000, 'amf_ue_ngap_id': 15000}}}
    assert len(s.amf_contexts) == 1
    
    s.hook_core_amf_info_remove_ran(
        suci=a.get("suci", None),
        supi=a.get("supi", None),
        home_plmn_id=a.get("home_plmn_id", None),
        current_guti_plmn=a.get("current-guti", {}).get("plmn_id", None),
        current_guti_amf_id=a.get("current-guti", {}).get("amf_id", None),
        current_guti_m_tmsi=a.get("current-guti", {}).get("m_tmsi", None),
        next_guti_plmn=a.get("next-guti", {}).get("plmn_id", None),
        next_guti_amf_id=a.get("next-guti", {}).get("amf_id", None),
        next_guti_m_tmsi=a.get("next-guti", {}).get("m_tmsi", None),
        tai_plmn=a.get("nr_tai", {}).get("plmn_id", None),
        tai_tac=a.get("nr_tai", {}).get("tac", None),
        cgi_plmn=a.get("nr_cgi", {}).get("plmn_id", None),
        cgi_cellid=a.get("nr_cgi", {}).get("cell_id", None)
    )
    assert uectx is not None and asdict(uectx) == {'du_index': {'src': 'du1', 'idx': 100}, 'cucp_index': {'src': 'cucp1', 'idx': 200}, 
                                                   'cuup_index': None, 
                                                   'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20000}, 'nci': 201, 'tac': 12, 
                                                   'e1_bearers': [], 'tmsi': None, 'ngap_ids': {'ran_ue_ngap_id': 5000, 'amf_ue_ngap_id': 15000},
                                                   'core_amf_context_index': None, 'core_amf_info': None}
    num_amf_contexts_associated_with_ue = sum(1 for v in s.amf_contexts.values() if v[0] is not None)
    
    ## Add it again
    a = examples_with_matching_ngap
    s.hook_core_amf_info(
        ran_ue_ngap_id=a.get("ran_ue", {}).get("ran_ue_ngap_id", None),
        amf_ue_ngap_id=a.get("ran_ue", {}).get("amf_ue_ngap_id", None),
        suci=a.get("suci", None),
        supi=a.get("supi", None),
        home_plmn_id=a.get("home_plmn_id", None),
        current_guti_plmn=a.get("current-guti", {}).get("plmn_id", None),
        current_guti_amf_id=a.get("current-guti", {}).get("amf_id", None),
        current_guti_m_tmsi=a.get("current-guti", {}).get("m_tmsi", None),
        next_guti_plmn=a.get("next-guti", {}).get("plmn_id", None),
        next_guti_amf_id=a.get("next-guti", {}).get("amf_id", None),
        next_guti_m_tmsi=a.get("next-guti", {}).get("m_tmsi", None),
        tai_plmn=a.get("nr_tai", {}).get("plmn_id", None),
        tai_tac=a.get("nr_tai", {}).get("tac", None),
        cgi_plmn=a.get("nr_cgi", {}).get("plmn_id", None),
        cgi_cellid=a.get("nr_cgi", {}).get("cell_id", None)
    )
    uectx = s.getue_by_id(0)  
    assert uectx is not None and asdict(uectx) == {'du_index': {'src': 'du1', 'idx': 100}, 'cucp_index': {'src': 'cucp1', 'idx': 200}, 'cuup_index': None, 'ran_unique_ue_id': {'plmn': 101, 'pci': 400, 'crnti': 20000}, 'nci': 201, 'tac': 12, 'e1_bearers': [], 'tmsi': None, 'ngap_ids': {'ran_ue_ngap_id': 5000, 'amf_ue_ngap_id': 15000}, 'core_amf_context_index': 0, 'core_amf_info': {'suci': 'suci-0-001-01-0000-0-0-1230010004', 'supi': 'imsi-001011230010004', 'home_plmn_id': '001F01', 'current_guti': {'plmn_id': '999F99', 'amf_id': '20040', 'mtmsi': 3221226075}, 'next_guti': {'plmn_id': '999F99', 'amf_id': '20040', 'mtmsi': 3221225666}, 'tai': {'plmn_id': '00f110', 'tac': '1'}, 'cgi': {'plmn_id': '00f110', 'cell_id': '66c000'}, 'ngap_ids': {'ran_ue_ngap_id': 5000, 'amf_ue_ngap_id': 15000}}}
    assert len(s.amf_contexts) == 1
    num_amf_contexts_associated_with_ue = sum(1 for v in s.amf_contexts.values() if v[0] is not None)
    assert num_amf_contexts_associated_with_ue == 1

    # delete the UE
    ue_id = s.getid_by_du_index(du_src, du_index)
    ue = s.getue_by_id(ue_id)
    s.hook_du_ue_ctx_deletion(  du_src, du_index )
    s.hook_cucp_uemgr_ue_remove(   cucp_src, cucp_index )

    ctx = s.getue_by_id(ue_id)
    assert ctx is None
    assert s.get_num_contexts() == 0
    assert len(s.amf_contexts) == 1
    num_amf_contexts_associated_with_ue = sum(1 for v in s.amf_contexts.values() if v[0] is not None)
    assert num_amf_contexts_associated_with_ue == 0


    ## re-add UE
    s.hook_du_ue_ctx_creation(  du_src, 
                                du_index,
                                plmn,
                                pci,
                                crnti,
                                tac,
                                nci)
    s.hook_cucp_uemgr_ue_add(   cucp_src, 
                                cucp_index,
                                plmn,
                                pci,
                                crnti)

    ue_id = s.getid_by_du_index(du_src, du_index)
    ctx = s.getue_by_id(ue_id)
    assert ctx is not None
    assert s.get_num_contexts() == 1
    assert len(s.amf_contexts) == 1
    num_amf_contexts_associated_with_ue = sum(1 for v in s.amf_contexts.values() if v[0] is not None)
    assert num_amf_contexts_associated_with_ue == 0

    tmsi = 3221225666

    s.add_tmsi(cucp_src, cucp_index, tmsi) 

    # print("#############################################################################")
    # print("# delete s and start fresh")
    s = UeContextsMap(dbg=dbg)

    tnow = dt.datetime.now(dt.UTC)

    ## re-add UE
    s.hook_du_ue_ctx_creation(  du_src, 
                                du_index,
                                plmn,
                                pci,
                                crnti,
                                tac,
                                nci, 
                                now=tnow)
    s.hook_cucp_uemgr_ue_add(   cucp_src, 
                                cucp_index,
                                plmn,
                                pci,
                                crnti, 
                                now=tnow)
    s.add_tmsi(cucp_src, cucp_index, tmsi, now=tnow) 

    core_info_example2 = {
        "suci": "suci-0-001-01-0000-0-0-1230010004", "supi": "imsi-001011230010004", "home_plmn_id": "001F01", 
        "current-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221226075 }, 
        "next-guti": { "plmn_id": "999F99", "amf_id": "20040", "m_tmsi": 3221225666 }, 
        "nr_tai": { "plmn_id": "00f110", "tac": "1" }, 
        "nr_cgi": { "plmn_id": "00f110", "cell_id": "66c000" }, 
        "ran_ue": {"ran_ue_id": 36, "ran_ue_ngap_id": ngap_ran_ue_id, "amf_ue_ngap_id": ngap_amf_ue_id}}
    a = core_info_example2
    s.hook_core_amf_info(
        ran_ue_ngap_id=a.get("ran_ue", {}).get("ran_ue_ngap_id", None),
        amf_ue_ngap_id=a.get("ran_ue", {}).get("amf_ue_ngap_id", None),
        suci=a.get("suci", None),
        supi=a.get("supi", None),
        home_plmn_id=a.get("home_plmn_id", None),
        current_guti_plmn=a.get("current-guti", {}).get("plmn_id", None),
        current_guti_amf_id=a.get("current-guti", {}).get("amf_id", None),
        current_guti_m_tmsi=a.get("current-guti", {}).get("m_tmsi", None),
        next_guti_plmn=a.get("next-guti", {}).get("plmn_id", None),
        next_guti_amf_id=a.get("next-guti", {}).get("amf_id", None),
        next_guti_m_tmsi=a.get("next-guti", {}).get("m_tmsi", None),
        tai_plmn=a.get("nr_tai", {}).get("plmn_id", None),
        tai_tac=a.get("nr_tai", {}).get("tac", None),
        cgi_plmn=a.get("nr_cgi", {}).get("plmn_id", None),
        cgi_cellid=a.get("nr_cgi", {}).get("cell_id", None),
        now=tnow
    )

    ue_id = s.getid_by_du_index(du_src, du_index)
    ctx = s.getue_by_id(ue_id)
    assert ctx is not None
    assert s.get_num_contexts() == 1
    assert len(s.amf_contexts) == 1
    num_amf_contexts_associated_with_ue = sum(1 for v in s.amf_contexts.values() if v[0] is not None)
    assert num_amf_contexts_associated_with_ue == 1
    assert ctx.tmsi==tmsi and ctx.core_amf_context_index==0 and ctx.core_amf_info.next_guti.mtmsi==tmsi
    amf_id = s.get_amfid_by_tmsi(tmsi)
    assert amf_id is not None
    amf_info = s.amf_contexts[amf_id]
    assert amf_info[0] == ue_id

    ue_id = s.getid_by_du_index(du_src, du_index)
    ue = s.getue_by_id(ue_id)
    s.hook_du_ue_ctx_deletion(  du_src, du_index, now=tnow)
    s.hook_cucp_uemgr_ue_remove(   cucp_src, cucp_index, now=tnow)

    s.process_timeout(now=tnow+dt.timedelta(seconds=100))
    num_amf_contexts_associated_with_ue = sum(1 for v in s.amf_contexts.values() if v[0] is not None)
    assert num_amf_contexts_associated_with_ue == 0
    num_amf_contexts_disassociated_with_ue = sum(1 for v in s.amf_contexts.values() if v[2] is not None)
    assert len(s.amf_contexts) == 1
    assert num_amf_contexts_disassociated_with_ue == 1

    s.process_timeout(now=tnow+dt.timedelta(seconds=21599))
    num_amf_contexts_disassociated_with_ue = sum(1 for v in s.amf_contexts.values() if v[2] is not None)
    assert len(s.amf_contexts) == 1
    assert num_amf_contexts_disassociated_with_ue == 1

    s.process_timeout(now=tnow+dt.timedelta(seconds=21600))
    num_amf_contexts_disassociated_with_ue = sum(1 for v in s.amf_contexts.values() if v[2] is not None)
    assert len(s.amf_contexts) == 0

    print("\n\n------ All tests passed ---------")

    sys.exit(0)

