import datetime as dt
import hashlib
import hmac
import base64
import subprocess
import tempfile
import json

import atexit
from dataclasses import dataclass, asdict

##########################################
@dataclass()
class LaLoggerConfig:
    log_type: str
    workspace_id: str
    primary_key: str
    batch_max_num_packets: int
    batch_max_num_bytes: int
    batch_timeout_secs: int
    stats_periodicity_secs: int

    def __str__(self):
        return (
            f"log_type={self.log_type}, workspace_id={self.workspace_id}, "
            f"primary_key=******, batch_max_num_packets={self.batch_max_num_packets}, "
            f"batch_max_num_bytes={self.batch_max_num_bytes}, "
            f"batch_timeout_secs={self.batch_timeout_secs},"
            f"stats_periodicity_secs={self.stats_periodicity_secs}"
        )


##########################################
@dataclass()
class LaLoggerStats:
    msgs_sent: int
    bytes_sent: int
    msgs_dropped: int
    bytes_dropped: int


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

        self.next_stats_report_ts = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=self.cfg.stats_periodicity_secs)
        self.stats = LaLoggerStats(0, 0, 0, 0)

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
            self.flush_batch(batch_len_exceeded=((total_batch_len + len_msg) > self.cfg.batch_max_num_bytes))

        if len(self.batch) == 0:
            self.batch_start_time = dt.datetime.now(dt.timezone.utc)

        # add message to batch
        self.batch.append(msg)
        self.batch_payload_bytes += len_msg
    
        if self.dbg:
            print(f"LaLogger():process_msg: len batch -> {len(self.batch)} bytes={self.batch_payload_bytes} ")

        self.report_stats()
 
    ############################################
    def process_timeout(self):
        
        if len(self.batch) == 0:
            return
        
        # has batch_timeout_secs expired
        now = dt.datetime.now(dt.timezone.utc)
        if (now - self.batch_start_time).total_seconds() < self.cfg.batch_timeout_secs:
            return
        
        self.flush_batch()

        self.report_stats()

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
    def post_it(self, uri, data, headers) -> bool:
        try:
            # Due to a known issue with using the "requests" module with python sub-interpreters, a curl command is run instead.

            with tempfile.NamedTemporaryFile(delete=True) as tmp:
                tmp.write(data.encode('utf-8'))
                tmp.flush()  # Ensure data is written

                curl_timeout = (self.cfg.batch_timeout_secs - 1) if self.cfg.batch_timeout_secs > 4 else 4
              
                cmd = ["curl", "-X", "POST", uri, "-H", f"Content-Type: {headers['content-type']}", 
                    "-H", f"Authorization: {headers['Authorization']}", 
                    "-H", f"Log-Type: {headers['Log-Type']}", 
                    "-H", f"x-ms-date: {headers['x-ms-date']}", 
                    "--data-binary",  f"@{tmp.name}",
                    "--max-time", f"{curl_timeout}"  
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    print(
                        f"**** Log Analytics error, curl command failed: code: {result.returncode} error: {result.stderr}", flush=True
                    )
                    return False

                return True

        except Exception as e:
            print(f"**** Log Analytics exception: {e}", flush=True)
            return False

    ############################################
    def post_data(self, data) -> bool:
    
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
        return self.post_it(uri, data, headers)

    ############################################
    def flush_batch(self, batch_len_exceeded: bool = False):
        if self.batch_payload_bytes == 0:
            return

        if self.dbg:
            print(
                f"LaLogger():flush_batch: len batch -> {len(self.batch)} bytes={self.batch_payload_bytes} ", flush=True
            )

        # create batch message
        s = "[" + ",".join(self.batch) + "]"

        result = self.post_data(s)

        if result is True:
            # successfully sent, reset batch

            self.stats.msgs_sent += len(self.batch)
            self.stats.bytes_sent += len(s)

            # reset batch
            self.batch = []
            self.batch_payload_bytes = 0
            self.batch_start_time = None

        else:

            # failed to send
            
            # if batch_len_exceeded is True then drop the batch
            # else keep the batch for next time
            if batch_len_exceeded:
                print("**** Log Analytics error:   batch length exceeded, dropping batch", flush=True)

                self.stats.msgs_dropped += len(self.batch)
                self.stats.bytes_dropped += len(data)

                self.batch = []
                self.batch_payload_bytes = 0
                self.batch_start_time = None
            else:
                print("**** Log Analytics error:   keeping batch for next transmission", flush=True)

    ############################################
    def report_stats(self):

        now = dt.datetime.now(dt.timezone.utc)
        if now > self.next_stats_report_ts:

            timestamp = now.isoformat(
                "T", "microseconds"
            )
            
            prefix = f"{timestamp} : "
            stats = {
                "LogAnalyticsStats": asdict(self.stats) 
            }
            s = prefix + json.dumps(stats) 
            print(s)

            self.next_stats_report_ts = now + dt.timedelta(seconds=self.cfg.stats_periodicity_secs)
            self.stats = LaLoggerStats(0, 0, 0, 0)


    ############################################
    def __close(self):
        print("LaLogger(): __close")
        self.flush_batch()