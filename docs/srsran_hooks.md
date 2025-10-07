- [1. Introduction](#1-introduction)
- [2. XRAN](#2-xran)
  - [2.1. capture\_xran\_packet](#21-capture_xran_packet)
- [3. FAPI](#3-fapi)
  - [3.1. PHY-MAC hooks](#31-phy-mac-hooks)
    - [3.1.1. __fapi\_rx\_data\_indication__](#311-fapi_rx_data_indication)
    - [3.1.2. __fapi\_crc\_indication__](#312-fapi_crc_indication)
    - [3.1.3. __fapi\_uci\_indication__](#313-fapi_uci_indication)
    - [3.1.4. __fapi\_srs\_indication__](#314-fapi_srs_indication)
    - [3.1.5. __fapi\_rach\_indication__](#315-fapi_rach_indication)
  - [3.2. MAC-PHY](#32-mac-phy)
    - [3.2.1. __fapi\_dl\_tti\_request__](#321-fapi_dl_tti_request)
    - [3.2.2. __fapi\_ul\_tti\_request__](#322-fapi_ul_tti_request)
    - [3.2.3. __fapi\_ul\_dci\_request__](#323-fapi_ul_dci_request)
    - [3.2.4. __fapi\_tx\_data\_request__](#324-fapi_tx_data_request)
- [4. DU UE context creation/deletion](#4-du-ue-context-creationdeletion)
  - [4.1. __du\_ue\_ctx\_creation__](#41-du_ue_ctx_creation)
  - [4.2. __du\_ue\_ctx\_update\_crnti__](#42-du_ue_ctx_update_crnti)
  - [4.3. __du\_ue\_ctx\_deletion__](#43-du_ue_ctx_deletion)
- [5. MAC scheduler](#5-mac-scheduler)
  - [5.1. MAC scheduler context creation/deletion](#51-mac-scheduler-context-creationdeletion)
    - [5.1.1. __mac\_sched\_ue\_creation__](#511-mac_sched_ue_creation)
    - [5.1.2. __mac\_sched\_ue\_reconfig__](#512-mac_sched_ue_reconfig)
    - [5.1.3. __mac\_sched\_ue\_deletion__](#513-mac_sched_ue_deletion)
    - [5.1.4. __mac\_sched\_ue\_config\_applied__](#514-mac_sched_ue_config_applied)
  - [5.2. MAC scheduler input data](#52-mac-scheduler-input-data)
    - [5.2.1. __mac\_sched\_ul\_bsr\_indication__](#521-mac_sched_ul_bsr_indication)
    - [5.2.2. __mac\_sched\_crc\_indication__](#522-mac_sched_crc_indication)
    - [5.2.3. __mac\_sched\_uci\_indication__](#523-mac_sched_uci_indication)
    - [5.2.4. __mac\_sched\_dl\_mac\_ce\_indication__](#524-mac_sched_dl_mac_ce_indication)
    - [5.2.5. __mac\_sched\_ul\_phr\_indication__](#525-mac_sched_ul_phr_indication)
    - [5.2.6. __mac\_sched\_dl\_buffer\_state\_indication__](#526-mac_sched_dl_buffer_state_indication)
    - [5.2.7. __mac\_sched\_srs\_indication__](#527-mac_sched_srs_indication)
- [6. PDCP](#6-pdcp)
  - [6.1. PDCP downlink](#61-pdcp-downlink)
    - [6.1.1. __pdcp\_dl\_creation__](#611-pdcp_dl_creation)
    - [6.1.2. __pdcp\_dl\_deletion__](#612-pdcp_dl_deletion)
    - [6.1.3. __pdcp\_dl\_new\_sdu__](#613-pdcp_dl_new_sdu)
    - [6.1.4. __pdcp\_dl\_tx\_data\_pdu__](#614-pdcp_dl_tx_data_pdu)
    - [6.1.5. __pdcp\_dl\_tx\_control\_pdu__](#615-pdcp_dl_tx_control_pdu)
    - [6.1.6. __pdcp\_dl\_handle\_tx\_notification__](#616-pdcp_dl_handle_tx_notification)
    - [6.1.7. __pdcp\_dl\_handle\_delivery\_notification__](#617-pdcp_dl_handle_delivery_notification)
    - [6.1.8. __pdcp\_dl\_discard\_pdu__](#618-pdcp_dl_discard_pdu)
    - [6.1.9. __pdcp\_dl\_reestablish__](#619-pdcp_dl_reestablish)
  - [6.2. PDCP uplink](#62-pdcp-uplink)
    - [6.2.1. __pdcp\_ul\_creation__](#621-pdcp_ul_creation)
    - [6.2.2. __pdcp\_ul\_deletion__](#622-pdcp_ul_deletion)
    - [6.2.3. __pdcp\_ul\_rx\_data\_pdu__](#623-pdcp_ul_rx_data_pdu)
    - [6.2.4. __pdcp\_ul\_rx\_control\_pdu__](#624-pdcp_ul_rx_control_pdu)
    - [6.2.5. __pdcp\_ul\_deliver\_sdu__](#625-pdcp_ul_deliver_sdu)
    - [6.2.6. __pdcp\_ul\_reestablish__](#626-pdcp_ul_reestablish)
- [7. E1AP procedures](#7-e1ap-procedures)
  - [7.1. E1AP CUCP hooks](#71-e1ap-cucp-hooks)
    - [7.1.1. __e1\_cucp\_bearer\_context\_setup__](#711-e1_cucp_bearer_context_setup)
    - [7.1.2. __e1\_cucp\_bearer\_context\_modification__](#712-e1_cucp_bearer_context_modification)
    - [7.1.3. __e1\_cucp\_bearer\_context\_delete__](#713-e1_cucp_bearer_context_delete)
    - [7.1.4. __e1\_cucp\_bearer\_context\_release__](#714-e1_cucp_bearer_context_release)
  - [7.2. E1AP CUUP hooks](#72-e1ap-cuup-hooks)
    - [7.2.1. __e1\_cuup\_bearer\_context\_setup__](#721-e1_cuup_bearer_context_setup)
    - [7.2.2. __e1\_cuup\_bearer\_context\_modification__](#722-e1_cuup_bearer_context_modification)
    - [7.2.3. __e1\_cuup\_bearer\_context\_release__](#723-e1_cuup_bearer_context_release)
- [8. CUCP UE Context Management](#8-cucp-ue-context-management)
  - [8.1. __cucp\_uemgr\_ue\_add__](#81-cucp_uemgr_ue_add)
  - [8.2. __cucp\_uemgr\_ue\_update__](#82-cucp_uemgr_ue_update)
  - [8.3. __cucp\_uemgr\_ue\_remove__](#83-cucp_uemgr_ue_remove)
- [9. NGAP](#9-ngap)
  - [9.1. __ngap\_procedure\_started__](#91-ngap_procedure_started)
  - [9.2. __ngap\_procedure\_completed__](#92-ngap_procedure_completed)
  - [9.3. __ngap\_procedure\_reset__](#93-ngap_procedure_reset)
- [10. RRC](#10-rrc)
  - [10.1. __rrc\_ue\_add__](#101-rrc_ue_add)
  - [10.2. __rrc\_ue\_update\_context__](#102-rrc_ue_update_context)
  - [10.3. __rrc\_ue\_update\_id__](#103-rrc_ue_update_id)
  - [10.4. __rrc\_ue\_remove__](#104-rrc_ue_remove)
  - [10.5. __rrc\_ue\_procedure\_started__](#105-rrc_ue_procedure_started)
  - [10.6. __rrc\_ue\_procedure\_completed__](#106-rrc_ue_procedure_completed)
- [11. RLC](#11-rlc)
  - [11.1. RLC downlink](#111-rlc-downlink)
    - [11.1.1. __rlc\_dl\_creation__](#1111-rlc_dl_creation)
    - [11.1.2. __rlc\_dl\_deletion__](#1112-rlc_dl_deletion)
    - [11.1.3. __rlc\_dl\_new\_sdu__](#1113-rlc_dl_new_sdu)
    - [11.1.4. __rlc\_dl\_lost\_sdu__](#1114-rlc_dl_lost_sdu)
    - [11.1.5. __rlc\_dl\_discard\_sdu__](#1115-rlc_dl_discard_sdu)
    - [11.1.6. __rlc\_dl\_sdu\_send\_started__](#1116-rlc_dl_sdu_send_started)
    - [11.1.7. __rlc\_dl\_sdu\_send\_completed__](#1117-rlc_dl_sdu_send_completed)
    - [11.1.8. __rlc\_dl\_sdu\_delivered__](#1118-rlc_dl_sdu_delivered)
    - [11.1.9. __rlc\_dl\_tx\_pdu__](#1119-rlc_dl_tx_pdu)
    - [11.1.10. __rlc\_dl\_rx\_status__](#11110-rlc_dl_rx_status)
    - [11.1.11. __rlc\_dl\_am\_tx\_pdu\_retx\_count__](#11111-rlc_dl_am_tx_pdu_retx_count)
    - [11.1.12. __rlc\_dl\_am\_tx\_pdu\_max\_retx\_count\_reached__](#11112-rlc_dl_am_tx_pdu_max_retx_count_reached)
  - [11.2. RLC uplink](#112-rlc-uplink)
    - [11.2.1. __rlc\_ul\_creation__](#1121-rlc_ul_creation)
    - [11.2.2. __rlc\_ul\_deletion__](#1122-rlc_ul_deletion)
    - [11.2.3. __rlc\_ul\_rx\_pdu__](#1123-rlc_ul_rx_pdu)
    - [11.2.4. __rlc\_ul\_sdu\_recv\_started__](#1124-rlc_ul_sdu_recv_started)
    - [11.2.5. __rlc\_ul\_sdu\_delivered__](#1125-rlc_ul_sdu_delivered)
- [12. Periodic performance hook](#12-periodic-performance-hook)
  - [12.1. report\_stats](#121-report_stats)



# 1. Introduction

Numerous Jbpf hooks have been added to the srsRAN codebase.

When a codelet is called, all parameters are passed in a "context" parameter.
The following sections describe the hooks, along with the "context" details.
The hook names are listed in bullets in the sections below.

# 2. XRAN

## 2.1. capture_xran_packet

Context info:  
```c
    data: pointer to start of the XRAN packet
    data_end: pointer to end of the XRAN packet
    direction: 0-tx, 1=rx
```

# 3. FAPI

Context info:  
```c
    cell_id: Cell identifier
    data: pointer to start of the FAPI message
    data_end: pointer to end of the FAPI message
```

## 3.1. PHY-MAC hooks

### 3.1.1. __fapi_rx_data_indication__
    
  Context "data" field points to a fapi::rx_data_indication_message structure.
  
### 3.1.2. __fapi_crc_indication__
       
  Context "data" field points to a fapi::crc_indication_message structure.

### 3.1.3. __fapi_uci_indication__

  Context "data" field points to a fapi::uci_indication_message structure.

### 3.1.4. __fapi_srs_indication__
  
  Context "data" field points to a fapi::srs_indication_message structure.

### 3.1.5. __fapi_rach_indication__
 
  Context "data" field points to a fapi::rach_indication_message structure.


## 3.2. MAC-PHY
 
### 3.2.1. __fapi_dl_tti_request__
  
  Context "data" field points to a fapi::dl_tti_request_message structure.
  
### 3.2.2. __fapi_ul_tti_request__
  
  Context "data" field points to a fapi::ul_tti_request_message structure.

### 3.2.3. __fapi_ul_dci_request__
  
  Context "data" field points to a fapi::ul_dci_request_message structure.
  
### 3.2.4. __fapi_tx_data_request__
  
  Context "data" field points to a fapi::tx_data_request_message structure.


# 4. DU UE context creation/deletion

These hooks have information passed in using a __jbpf_du_ue_ctx_info__ as shown below ..
```c
    struct jbpf_du_ue_ctx_info {
        uint16_t ctx_id;   /* Context id (could be implementation specific) */
        uint32_t du_ue_index;
        uint32_t tac;
        uint32_t plmn;
        uint64_t nci;
        uint16_t pci;
        uint16_t crnti;
    };
```

Context info:  
```
    data: pointer to the jbpf_du_ue_ctx_info
    data_end: pointer to end of the jbpf_du_ue_ctx_info
```

## 4.1. __du_ue_ctx_creation__
  
## 4.2. __du_ue_ctx_update_crnti__
  
## 4.3. __du_ue_ctx_deletion__
  

# 5. MAC scheduler

## 5.1. MAC scheduler context creation/deletion

These hooks are called when a scheduler context is created/updated/deleted.

Context info:  
```
    du_ue_index: The index used in the DU entity to identify the UE
```

### 5.1.1. __mac_sched_ue_creation__
  
### 5.1.2. __mac_sched_ue_reconfig__
  
### 5.1.3. __mac_sched_ue_deletion__
  
### 5.1.4. __mac_sched_ue_config_applied__
  

## 5.2. MAC scheduler input data

These hooks are called when a scheduler receives information e.g. Buffer-Status-Reports, Power-Headroom-Reports etc.

Context info:  
```
    du_ue_index: The index used in the DU entity to identify the UE
    data: pointer to start of the scheduler input message
    data_end: pointer to end of the scheduler input message

```

### 5.2.1. __mac_sched_ul_bsr_indication__
  
    Context "data" field points to an srsran::ul_bsr_indication_message structure.

### 5.2.2. __mac_sched_crc_indication__
  
    Context "data" field points to an srsran::ul_crc_pdu_indication structure.
  
### 5.2.3. __mac_sched_uci_indication__
  
    Context "data" field points to an srsran::uci_indication::uci_pdu structure.
  
### 5.2.4. __mac_sched_dl_mac_ce_indication__
  
    Context "data" field points to an srsran::dl_mac_ce_indication structure.
  
### 5.2.5. __mac_sched_ul_phr_indication__
  
    Context "data" field points to an srsran::cell_ph_report structure.
  
### 5.2.6. __mac_sched_dl_buffer_state_indication__
  
    Context "data" field points to an srsran::dl_buffer_state_indication_message structure.
  
### 5.2.7. __mac_sched_srs_indication__
  
    Context "data" field points to an srsran::srs_indication::srs_indication_pdu structure.

# 6. PDCP

These hooks have information passed in using a __jbpf_pdcp_ctx_info__ as shown below ..
```c
    typedef struct {
        uint8_t used;      /* Is the window used, 0 = not-used, 1 = used */
        uint32_t num_pkts;     /* Total packets */
        uint32_t num_bytes;    /* Total bytes*/
    } jbpf_queue_info_t;

    struct jbpf_pdcp_ctx_info {
        uint16_t ctx_id;   /* Context id (could be implementation specific) */
        uint32_t cu_ue_index;   /* if is_srb=True is cu_cp_ue_index, if is_srb=False is cu_up_ue_index */
        uint8_t is_srb; /* true=srb, false=drb */
        uint8_t rb_id;   /* if is_srb=True:    0=srb0, 1=srb1, 2=srb2,
                            if is_srb=False:   1=drb1, 2=drb2, 3-drb3 ... */
        uint8_t rlc_mode;  /* 0=UM, 1=AM*/
        // window details
        jbpf_queue_info_t window_info;  /* Window info */        
    };
```

## 6.1. PDCP downlink

### 6.1.1. __pdcp_dl_creation__
     
    Called when a downlink PDCP bearer is created.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

### 6.1.2. __pdcp_dl_deletion__
      
    Called when a downlink PDCP bearer is deleted.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

### 6.1.3. __pdcp_dl_new_sdu__
     
    Called when a new SDU is received from higher layers.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1:  sdu_length << 32 | count
    ```

### 6.1.4. __pdcp_dl_tx_data_pdu__
     
    Called when a PDCP data PDU is sent to RLC.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1 = pdu_length << 32 | count;
        srs_meta_data2 = is_retx << 32 | latency_set
        srs_meta_data3 = latency_ns   // from sdu-arrival to transmission of the PDU
    ```

### 6.1.5. __pdcp_dl_tx_control_pdu__
  
    Called when a PDCP control PDU is sent to RLC.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1 = pdu_length 
    ```

### 6.1.6. __pdcp_dl_handle_tx_notification__
  
    This is a notification when first byte of a PDCP SDU is transmitted by RLC.
   
    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1 = notif_count
    ```

    Note that the notif_count means "up to and including" that count. i.e. in the following example

            pdcp_dl_handle_tx_notification notif_count=0

            pdcp_dl_handle_tx_notification notif_count=1

            pdcp_dl_handle_tx_notification notif_count=5

    the last message means that counts 2-5 are all being notified.

### 6.1.7. __pdcp_dl_handle_delivery_notification__
  
    In RLC TM/UM mode, this is a notificaion when all bytes of a PDCP SDU have been sent to lower layers.
    
    In RLC AM mode, this is a notificaion when all bytes of a PDCP SDU have been sent to lower layers, and acknowledged by the UE.
    
    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1 = notif_count 
    ```

    Note that the notif_count means "up to and including" that count. i.e. in the following example

           pdcp_dl_handle_delivery_notification notif_count=0

           pdcp_dl_handle_delivery_notification notif_count=1

           pdcp_dl_handle_delivery_notification notif_count=5

    the last message means that counts 2-5 are all being notified.

### 6.1.8. __pdcp_dl_discard_pdu__

    Called when an SDU is discarded by the PDCP layer

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1 = count <<
    ```

### 6.1.9. __pdcp_dl_reestablish__

    Called when a PDCP DL bearer is restablished.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

## 6.2. PDCP uplink

### 6.2.1. __pdcp_ul_creation__
     
    Called when a uplink PDCP bearer is created.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

### 6.2.2. __pdcp_ul_deletion__
      
    Called when a uplink PDCP bearer is deleted.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

### 6.2.3. __pdcp_ul_rx_data_pdu__
      
    Called when a uplink PDCP data PDU is received from lower layers.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1: pdu_length << 32 | header_length
        srs_meta_data2: count 
    ```

### 6.2.4. __pdcp_ul_rx_control_pdu__
      
    Called when a uplink PDCP control PDU is received from lower layers.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1: pdu_length
    ```

### 6.2.5. __pdcp_ul_deliver_sdu__
      
    Called when PDCP delivers an SDU to higher layers.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1: sdu_length 
    ```

### 6.2.6. __pdcp_ul_reestablish__

    Called when a PDCP DL bearer is restablished.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

# 7. E1AP procedures

## 7.1. E1AP CUCP hooks

These hooks have information passed in using a __jbpf_cucp_e1_ctx_info__ as shown below ..
```c
    struct jbpf_cucp_e1_ctx_info {
        uint16_t ctx_id;   /* Context id (could be implementation specific) */
        uint64_t cu_cp_ue_index; 
        uint64_t gnb_cu_cp_ue_e1ap_id; 
        uint64_t gnb_cu_up_ue_e1ap_id; 
    };
```

All of the CUCP hooks have this context.

    Context info:  
    ```
        data: pointer to the jbpf_cucp_e1_ctx_info
        data_end: pointer to end of the jbpf_cucp_e1_ctx_info
    ```

### 7.1.1. __e1_cucp_bearer_context_setup__
     
    Called when CUCP sends a setup request to CUUP.

### 7.1.2. __e1_cucp_bearer_context_modification__
     
    Called when CUCP sends a modification request to CUUP.

### 7.1.3. __e1_cucp_bearer_context_delete__
     
    Called when CUCP sends a delete request to CUUP.

### 7.1.4. __e1_cucp_bearer_context_release__
     
    Called when CUCP determines that a bearer is inactive.

## 7.2. E1AP CUUP hooks

These hooks have information passed in using a __jbpf_cuup_e1_ctx_info__ as shown below ..
```c
struct jbpf_cuup_e1_ctx_info {
    uint16_t ctx_id;   /* Context id (could be implementation specific) */
    uint64_t cu_up_ue_index; 
    uint64_t gnb_cu_cp_ue_e1ap_id; 
    uint64_t gnb_cu_up_ue_e1ap_id; 
};
```

All of the CUUP hooks have this context.

    Context info:  
    ```
        data: pointer to the jbpf_cuup_e1_ctx_info
        data_end: pointer to end of the jbpf_cuup_e1_ctx_info
        srs_meta_data1 = success/fail
    ```

### 7.2.1. __e1_cuup_bearer_context_setup__
     
    Called when CUUP processes a setup request from the CUCP.

### 7.2.2. __e1_cuup_bearer_context_modification__
     
    Called when CUUP processes a modification request from the CUCP.

### 7.2.3. __e1_cuup_bearer_context_release__
     
    Called when CUUP processes a release request from the CUCP.


# 8. CUCP UE Context Management

These hooks are called when UE contexts are created/upated/deleted in the CUCP.

These hooks have information passed in using a __jbpf_cucp_uemgr_ctx_info__ as shown below ..
```c
struct jbpf_cucp_uemgr_ctx_info {
    uint16_t ctx_id;    /* Context id (could be implementation specific) */
    uint16_t du_index;  
    uint32_t plmn;      /* (mcc << 16) || mnc */ 
    uint64_t cu_cp_ue_index; 
};
```

## 8.1. __cucp_uemgr_ue_add__
     
    Called when a new UE context is created.

    Context info:  
    ```
        data: pointer to the jbpf_cuup_e1_ctx_info
        data_end: pointer to end of the jbpf_cuup_e1_ctx_info
        srs_meta_data1 = pci_set << 16 | pci
        srs_meta_data2 = rnti_set << 16 | rnti
    ```

## 8.2. __cucp_uemgr_ue_update__
     
    Called when a new UE context is updated.

    Context info:  
    ```
        data: pointer to the jbpf_cuup_e1_ctx_info
        data_end: pointer to end of the jbpf_cuup_e1_ctx_info
        srs_meta_data1 = pci
        srs_meta_data2 = rnti
    ```

## 8.3. __cucp_uemgr_ue_remove__
     
    Called when a new UE context is deleted.

    Context info:  
    ```
        data: pointer to the jbpf_cuup_e1_ctx_info
        data_end: pointer to end of the jbpf_cuup_e1_ctx_info
    ```

# 9. NGAP

These hooks are called when NGAP procedures are execured.

These hooks have information passed in using a __jbpf_ngap_ctx_info__ as shown below ..
```c
struct jbpf_ngap_ctx_info {
    uint16_t ctx_id;    /* Context id (could be implementation specific) */
    uint64_t cucp_ue_index; 
    uint16_t ran_ue_ngap_id_set;
    uint64_t ran_ue_ngap_id; /* RAN UE NGAP ID */
    uint16_t amf_ue_ngap_id_set;
    uint64_t amf_ue_ngap_id; /* AMF UE NGAP ID */
};
```

The different procedures are identified by this enum ..
```c
typedef enum {
    NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP = 1,
    NGAP_PROCEDURE_UE_CONTEXT_RELEASE,
    NGAP_PROCEDURE_PDU_SESSION_SETUP,
    NGAP_PROCEDURE_PDU_SESSION_MODIFY,
    NGAP_PROCEDURE_PDU_SESSION_RELEASE,
    NGAP_PROCEDURE_RESOURCE_ALLOCATION,
    NGAP_PROCEDURE_MAX
} JbpfNgapProcedure_t;
```

## 9.1. __ngap_procedure_started__
     
    Called when an NGAP procedure is started.

    Context info:  
    ```
        data: pointer to the jbpf_ngap_ctx_info
        data_end: pointer to end of the jbpf_ngap_ctx_info
        srs_meta_data1: procedure (i.e. JbpfNgapProcedure_t)
    ```

## 9.2. __ngap_procedure_completed__
     
    Called when an NGAP procedure is completed.

    Context info:  
    ```
        data: pointer to the jbpf_ngap_ctx_info
        data_end: pointer to end of the jbpf_ngap_ctx_info
        srs_meta_data1: = success << 32 | procedure;
    ```

## 9.3. __ngap_procedure_reset__
     
    Called when an NGAP RESET occurs.

    Context info:  
    ```
        data: pointer to the jbpf_ngap_ctx_info
        data_end: pointer to end of the jbpf_ngap_ctx_info
    ```

# 10. RRC

These hooks are called when RRC procedures are execured.

These hooks have information passed in using a __jbpf_rrc_ctx_info__ as shown below ..
```c
struct jbpf_rrc_ctx_info {
    uint16_t ctx_id;    /* Context id (could be implementation specific) */
    uint64_t cu_cp_ue_index; 
};
```

The different procedures are identified by this enum ..
```c
typedef enum {
    RRC_SETUP = 1,
    RRC_RECONFIGURATION,
    RRC_REESTABLISHMENT,
    RRC_UE_CAPABILITY,
    RRC_PROCEDURE_MAX
} JbpfRrcProcedure_t;
```

## 10.1. __rrc_ue_add__
     
    Called when a UE entity is created in RRC.

    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
        srs_meta_data1 = (c_rnti << 48) | (pci << 32) | tac
        srs_meta_data2 = plmn
        srs_meta_data3 = nci
    ```

## 10.2. __rrc_ue_update_context__
     
    Called when a UE entity is updated in RRC.

    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
        srs_meta_data1: old_cu_ue_index;
        srs_meta_data2: (c_rnti << 48) | (pci << 32) | tac
        srs_meta_data3: plmn
        srs_meta_data4: nci;   
    ```

## 10.3. __rrc_ue_update_id__
     
    Called when a UE'd 5GTMSI is updated in RRC.

    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
        srs_meta_data1 =_5gtimsi;
    ```
    
## 10.4. __rrc_ue_remove__
     
    Called when a UE entity is deleted in RRC.

    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
    ```

## 10.5. __rrc_ue_procedure_started__
     
    Called when an RRC procedure is started.
       
    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
        srs_meta_data1: procedure (i.e JbpfRrcProcedure_t)
    ```

## 10.6. __rrc_ue_procedure_completed__
     
    Called when an RRC procedure is completed.
       
    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
        srs_meta_data1:srs_meta_data1 = (success << 32) | procedure;
    ```

# 11. RLC

These hooks have information passed in using a __jbpf_rlc_ctx_info__ as shown below ..
```c
    struct jbpf_rlc_ctx_info {
        uint16_t ctx_id;    /* Context id (could be implementation specific) */
        uint64_t gnb_du_id;
        uint16_t du_ue_index; 
        uint8_t is_srb;  /* true=srb, false=drb */
        uint8_t rb_id;   /* if is_srb=True:    0=srb0, 1=srb1, 2=srb2,
                        if is_srb=False:      1=drb1, 2=drb2, 3-drb3 ... */
        JbpfDirection_t direction; /* 0 DL, 1 UL */
        JbpfRlcMode_t rlc_mode;  /* 0=TM, 1=UM, 2=AM*/

        union {
            struct {
                jbpf_queue_info_t sdu_queue_info; /* SDU queue info */
            } tm_tx;
            struct {
                jbpf_queue_info_t sdu_queue_info; /* SDU queue info */
            } um_tx;
            struct {
                jbpf_queue_info_t sdu_queue_info; /* SDU queue info */
                jbpf_queue_info_t window_info;  /* Window info */
            } am_tx;
            struct {
                uint32_t window_num_pkts;  /* Window info */
            } um_rx;
            struct {
                uint32_t window_num_pkts;  /* Window info */
            } am_rx;
        } u;
    };
```

These enums are also used ..
```c
typedef enum {
    JBPF_RLC_MODE_TM = 1,
    JBPF_RLC_MODE_UM,
    JBPF_RLC_MODE_AM,
    JBPF_RLC_MODE_MAX
} JbpfRlcMode_t;

typedef enum {
    JBPF_RLC_PDUTYPE_STATUS = 1,
    JBPF_RLC_PDUTYPE_DATA,
    JBPF_RLC_PDUTYPE_DATA_RETX,
    JBPF_RLC_PDUTYPE_MAX
} JbpfRlcPdu_t;
```

## 11.1. RLC downlink

### 11.1.1. __rlc_dl_creation__
     
    Called when a downlink RLC bearer is created.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
    ```

### 11.1.2. __rlc_dl_deletion__
     
    Called when a downlink RLC bearer is deleted.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
    ```

### 11.1.3. __rlc_dl_new_sdu__
     
    Called when a new SDU is received from PDCP.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: sdu_length << 32 | pdcp_sn
        srs_meta_data2: is_retx
    ```

### 11.1.4. __rlc_dl_lost_sdu__
     
    Called when an SDU is dropped due to an internal overflow.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: sdu_length << 32 | pdcp_sn
        srs_meta_data2: is_retx
    ```

### 11.1.5. __rlc_dl_discard_sdu__
     
    Called when a SDU is discarded.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdcp_sn << 32 | success
    ```

### 11.1.6. __rlc_dl_sdu_send_started__
     
    Called when the first byte of an SDU is transmitted.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdcp_sn << 32 | is_retx
        srs_meta_data2: latency_ns  // time from sdu-arrival to start of transmission of the first byte 
    ```

### 11.1.7. __rlc_dl_sdu_send_completed__
     
    Called when all bytes of the SDU have been transmitted.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdcp_sn << 32 | is_retx
        srs_meta_data2: latency_ns  // time from sdu-arrival to when all bytes have been transmitted.
    ```

### 11.1.8. __rlc_dl_sdu_delivered__
     
    Called when all bytes of the SDU have been received by the peer RLC entity
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdcp_sn << 32 | is_retx
        srs_meta_data2: latency_ns   // time from sdu-arrival to when all bytes have been acknowledgd as received by the UE.
    ```

### 11.1.9. __rlc_dl_tx_pdu__
     
    Called when an RLC PDU is transmitted.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdu_type << 32 | pdu_len
    ```

### 11.1.10. __rlc_dl_rx_status__
     
    Called when a STATUS PDU is received from lower layers.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
    ```

### 11.1.11. __rlc_dl_am_tx_pdu_retx_count__
     
    Called when a PDU is retransmitted, ahd shows thw retx count.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: sn << 32 | retx_count
    ```

### 11.1.12. __rlc_dl_am_tx_pdu_max_retx_count_reached__
     
    Called when the maximum allowed RLC retransmissions is reached.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: sn << 32 | retx_count
    ```
## 11.2. RLC uplink

### 11.2.1. __rlc_ul_creation__
     
    Called when a uplink RLC bearer is created.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
    ```

### 11.2.2. __rlc_ul_deletion__
     
    Called when a uplink RLC bearer is deleted.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
    ```

### 11.2.3. __rlc_ul_rx_pdu__
     
    Called when a PDU is received from lower layers.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdu_type << 32 | pdu_len
    ```

### 11.2.4. __rlc_ul_sdu_recv_started__
     
    Called when a PDU is received for an SDU for which no bytes have previously been received.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1 = sn 
    ```

### 11.2.5. __rlc_ul_sdu_delivered__
     
    Called when an SDU is delivered to higher layers.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: sn << 32 | sdu_length
        srs_meta_data2: latency_ns // from start of SDU reception to SDU delivery
    ```

# 12. Periodic performance hook

## 12.1. report_stats

This is a predefine hook built into the Jbpf framework.
It is called invoked every second.

The information passed is shown below. However ***any codelet can be bound to this hook if a periodic trigger is required.***

The hook has information passed in using a _jbpf_perf_hook_list__ as shown below ..
```c
    struct jbpf_perf_data
    {
        uint64_t num;
        uint64_t min;
        uint64_t max;
        uint32_t hist[JBPF_NUM_HIST_BINS];
        jbpf_hook_name_t hook_name;
    };
    struct jbpf_perf_hook_list
    {
        uint8_t num_reported_hooks;
        struct jbpf_perf_data perf_data[MAX_NUM_HOOKS];
    } 
```

    Context info:  
    ```
        data: pointer to the jbpf_perf_hook_list
        data_end: pointer to end of the jbpf_perf_hook_list
        meas_period: Period of measurements in ms
    ```
