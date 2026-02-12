# Run the first example without *jrt-controller*

We will run the first example without *jrt-controller*. 

To start without *jrt-controller*, we need to set the env variable `USE_JRTC=0`. 
The default environment options are in file __".env"__. 
If you wish to override any of these variables, create a separate file called __".env.local"__, with variable which should be overwritten, for example:-

```sh
USE_JRTC=0
```

Now, let's build the codelets first:
```sh
cd codelets
./make.sh
```

Next, you need to open 3 terminal windows, one for the srsRAN, one for a message decoder, and one for loading/unloading codelets. 
In each window, set up the environment variables as described [here](./baremetal.md#set-required-environment-variables)

`Terminal-1`
In the srsRAN terminal, start the `gnb` binary in the usual way 

`Terminal-2`
In the message decoder window, you need to run the decoder application. 
This is an application to which schemas will be loaded, and it will printed the protobuf decode of messages it receives.
```sh
cd utils
./run_jbpf_decoder.sh
```
For more info on the message decoder, see [here](https://github.com/microsoft/jbpf-protobuf/blob/main/examples/first_example_standalone/README.md).

`Terminal-3`
Run the *jbpf* reverse proxy (see [here](https://github.com/microsoft/jbpf/tree/main/examples/reverse_proxy) for more info):
```sh
sudo -E $SRSRAN_DIR/out/bin/srsran_reverse_proxy --host-port 30450 --address "/tmp/jbpf/jbpf_lcm_ipc"
```

`Terminal-4`
Finally, in the last window, load the schemas and codelets (if you run your srsRAN with sudo, you'll need to run the above command with sudo):
```sh
cd utils
sudo -E ./load.sh -c $JBPF_CODELETS/xran_packets/xran_packets.yaml
```
In the srsRAN window you should see a bunch of messages, including the final confirmation: `Codeletset is loaded OK`

In the decoder window, you should see an output like this:
```
INFO[0078] {"timestamp":"1740588245768711680","ulPacketStats":{"dataPacketStats":{"PacketCount":11016,"PrbCount":"716496","packetInterArrivalInfo":{"hist":[0,0,422,2157,1874,4960,1444,0,0,0,1,1,0,54,59,44]}}},"dlPacketStats":{"dataPacketStats":{"PacketCount":60300,"PrbCount":"6391800","packetInterArrivalInfo":{"hist":[45126,96,3,0,0,0,6223,8651,0,0,0,0,0,201,0,0]}},"ctrlPacketStats":{"PacketCount":9692,"packetInterArrivalInfo":{"hist":[7240,971,28,18,16,1,0,0,0,0,1162,58,154,44,0,0]}}}}  streamUUID=75888bf1-b719-d53d-b10c-bccc9719021f
```

This prints various statistics about the xRAN fronthaul packets (see the [collection](codelets/xran_packets/xran_packets_collect.c) and [reporting](codelets/xran_packets/xran_packets_report.c) codelets for more details). 

To unload the codelets, type:
```sh
cd utils
sudo -E ./unload.sh -c $JBPF_CODELETS/xran_packets/xran_packets.yaml
```
