import datetime as dt
import hashlib
import hmac
import base64
import requests
import atexit
from dataclasses import dataclass


##########################################
@dataclass()
class LaLoggerConfig:
    log_type: str
    workspace_id: str
    primary_key: str
    batch_max_num_packets: int
    batch_max_num_bytes: int
    batch_timeout_secs: int

    def __str__(self):
        return (
            f"log_type={self.log_type}, workspace_id={self.workspace_id}, "
            f"primary_key=******, batch_max_num_packets={self.batch_max_num_packets}, "
            f"batch_max_num_bytes={self.batch_max_num_bytes}, "
            f"batch_timeout_secs={self.batch_timeout_secs}"
        )

#########################################################################################
class LaLogger:
    """Object to send messages to Log Analytics"""

    ############################################
    def __init__(self, cfg: LaLoggerConfig, dbg: bool = False):
        # initialisation

        self.cfg = cfg
        self.dbg = dbg  

        self.batch = []
        self.batch_payload_bytes = 0
        self.batch_start_time = None

        atexit.register(self.__close)

        if self.dbg:
            print(f"LaLogger(): __init__: cfg = {self.cfg} ", flush=True)

    ############################################
    def process_msg(self, msg):        

        len_msg = len(msg)

        total_batch_len = 0
        if len(self.batch) >= 0:
            total_batch_len = 2  # open and closing [ ]
            total_batch_len += len(self.batch) - 1  # commas
            total_batch_len += self.batch_payload_bytes

        # flush batch if adding this msg will cause the batch limits to be exceeded
        if ((len(self.batch) + 1) > self.cfg.batch_max_num_packets) or (
            (total_batch_len + len_msg) > self.cfg.batch_max_num_bytes
        ):
            self.flush_batch()

        if len(self.batch) == 0:
            self.batch_start_time = dt.datetime.now(dt.timezone.utc)

        # add message to batch
        self.batch.append(msg)
        self.batch_payload_bytes += len_msg
    
        if self.dbg:
            print(f"LaLogger():process_msg: len batch -> {len(self.batch)} bytes={self.batch_payload_bytes} ")
 
    ############################################
    def process_timeout(self):
        
        if len(self.batch) == 0:
            return
        
        # has batch_timeout_secs expired
        now = dt.datetime.now(dt.timezone.utc)
        if (now - self.batch_start_time).total_seconds() < self.cfg.batch_timeout_secs:
            return
        
        self.flush_batch()


    ############################################
    def LA_build_signature(self, date, content_length, method, content_type, resource):
        x_headers = "x-ms-date:" + date
        string_to_hash = (
            method
            + "\n"
            + str(content_length)
            + "\n"
            + content_type
            + "\n"
            + x_headers
            + "\n"
            + resource
        )
        bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
        decoded_key = base64.b64decode(self.cfg.primary_key)
        encoded_hash = base64.b64encode(
            hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()
        ).decode()
        authorization = "SharedKey {}:{}".format(self.cfg.workspace_id, encoded_hash)
        return authorization

    ############################################
    def post_it(self, uri, data, headers):
        response = requests.post(uri, data=data, headers=headers)
        if not (response.status_code >= 200 and response.status_code <= 299):
            if self.dbg:
                print(
                    f"**** Log Analytics error, response code: {response.status_code}"
                )

    ############################################
    def post_data(self, data):
    
        method = "POST"
        content_type = "application/json"
        resource = "/api/logs"
        rfc1123date = dt.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        content_length = len(data)
        signature = self.LA_build_signature(
            rfc1123date, content_length, method, content_type, resource
        )
        uri = (
            "https://"
            + self.cfg.workspace_id
            + ".ods.opinsights.azure.com"
            + resource
            + "?api-version=2016-04-01"
        )

        headers = {
            "content-type": content_type,
            "Authorization": signature,
            "Log-Type": self.cfg.log_type,
            "x-ms-date": rfc1123date,
        }

        self.post_it(uri, data, headers)

    ############################################
    def flush_batch(self):
        if self.batch_payload_bytes == 0:
            return

        if self.dbg:
            print(
                f"LaLogger():flush_batch: len batch -> {len(self.batch)} bytes={self.batch_payload_bytes} "
            )

        # create batch message
        s = "[" + ",".join(self.batch) + "]"

        self.post_data(s)

        # reset batch
        self.batch = []
        self.batch_payload_bytes = 0

        self.batch_start_time = None

    ############################################
    def __close(self):
        print("LaLogger(): __close")
        self.flush_batch()