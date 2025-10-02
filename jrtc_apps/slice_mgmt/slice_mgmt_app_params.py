
# Config for periodicity of sending SET request
slice_update_periodicity_secs = 60
# which SFN to perform the re-allocation.  "None" = immediately
slice_update_sfn = None
# which slot to perform the re-allocation.  "None" = immediately
# Note that if you select a slot which is not an downlink slot in the configured tdd pattern, the reconfig will never be triggered
slice_update_slot_index = 2     
# If slice_update_sfn=None and slice_update_slot_index=None, the reconfig config will be triggered on the next downlink slot


# Enable / Disable logging to Log Analytics
la_enabled = False
la_msgs_per_batch = 100
la_bytes_per_batch = 1024 * 1024  # 1 MB per batch
la_tx_timeout_secs = 5            # Timeout for batch sending (5 seconds)
la_stats_period_secs = 10

# Config for JSON port.
# This is used to receive data from the Core
json_udp_enabled = False
json_udp_port = 30502

