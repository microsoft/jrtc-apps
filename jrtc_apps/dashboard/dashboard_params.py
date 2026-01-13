
# Enable / Disable logging to Log Analytics
la_enabled = True
la_msgs_per_batch = 100
la_bytes_per_batch = 1024 * 1024  # 1 MB per batch
la_tx_timeout_secs = 5            # Timeout for batch sending (5 seconds)
la_stats_period_secs = 10

# Config for JSON port.
# This is used to receive data from the Core
json_udp_enabled = True
json_udp_port = 30502

# Enable/Disbale processing of individual part of the stack
include_ue_contexts = True
include_perf = True
include_rrc = True
include_ngap = True
include_pdcp = True
include_rlc = True
include_mac = True
include_fapi = True
include_xran = False
