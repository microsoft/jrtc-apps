#!/usr/bin/env python
#
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# Licensed under the Apache License, Version 2.0
#

import datetime as dt
import json


#########################################################################################
class Logger:
    """Object to manage log and rlogs"""

    # {
    ############################################
    def __init__(self, device, hostname, stream_id, stream_type, remote_logger=None):
        # print(f"logger(): __init__ : stream_id={stream_id} remote_logger={remote_logger}")
        # cfg
        self.device = device
        self.hostname = hostname
        self.stream_id = stream_id
        self.stream_type = stream_type
        self.remote_logger = remote_logger
        # initialisation
        self.sn = 0

    ############################################
    def log_msg(self, log, rlog, structure_type, msg, timestamp=None):

        if timestamp is None:
            timestamp = dt.datetime.now(dt.timezone.utc).isoformat(
                "T", "microseconds"
            )
        
        if log:
            prefix = "" if (timestamp is None) else f"{timestamp} : "
            s = prefix + msg
            print(s, flush=True)

        if rlog and (self.remote_logger is not None):
            
            j = {
                "device": self.device,
                "hostname": self.hostname,
                "stream_id": self.stream_id,
                "stream_type": self.stream_type,
                "stream_sn": int(self.sn),
                "stream_payload_structure": structure_type,
                "stream_payload_time": timestamp,
                "stream_payload_msg": msg,
            }

            # check if this is valid JSON
            try:
                j = json.dumps(j)
            except Exception as e:
                print(f"Logger():log_msg: Problem dumping to JSON: {j}, Error {e}")
                return

            self.remote_logger.process_msg(j)

            self.sn += 1 

   ############################################
    def process_timeout(self):
        if self.remote_logger is not None:
            self.remote_logger.process_timeout()

# }
