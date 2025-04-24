# Run the second example (with *jrt-controller*)

In this example we will use the xRAN codelets from the [example](./example_no_jrtc.md) without *jrt-controller*, and we will feed their input into a sample *jrt-controller* app. 

**Important:** There are several artifacts of the build that have to be rebuilt for different environments.   
If you switch from the example that doesn't use *jrt-controller* to the example that does, you need to make sure all of them are rebuilt. 
We advise you to do a clean clone of the repo in that case. 


### Configuring the components

To use *jrt-controller* with the examples in this repo, we need to set the env variable `USE_JRTC=1`. 
The default environment options are in file __".env"__. 
If you wish to override any of these variables, create a separate file called __".env.local"__, with variable which should be overwritten, for example:-
```sh
USE_JRTC=1
```
These overrides will occur when __set_vars.sh__ is executed.
You also need to define a path to your instance of jrt-controller, e.g.:
```sh
export JRTC_PATH=~/jrt-controller/
```
and then set the environment variables as described in the [README](../README.md). 


Next, you need to modify the srsRAN config file with the following section:
```yaml
jbpf:
  jbpf_run_path: "/tmp"
  jbpf_namespace: "jbpf"
  jbpf_enable_ipc: 1
  jbpf_standalone_io_out_ip: "127.0.0.1"
  jbpf_standalone_io_out_port: 20788
  jbpf_standalone_io_in_port: 30400
  jbpf_standalone_io_policy: 0
  jbpf_standalone_io_priority: 0
  jbpf_io_mem_size_mb: 1024
  jbpf_ipc_mem_name: "jrt_controller"
  jbpf_enable_lcm_ipc: 1
  jbpf_lcm_ipc_name: "jbpf_lcm_ipc"
  jbpf_agent_cpu: 0
  jbpf_agent_policy: 1
  jbpf_agent_priority: 30
  jbpf_maint_cpu: 0
  jbpf_maint_policy: 0
  jbpf_maint_priority: 0
```



#### Running the example

To run the example, we need 5 terminals. 
In each of these, you need to set the following environment variables:
```sh
export JRTC_PATH=~/jrt-controller/
export SRSRAN_DIR=~/srsRAN_Project/
export SRSRANAPP_DIR=~/jrtc-apps/
source $SRSRANAPP_DIR/set_vars.sh
```
The example uses sample path values. 
Please edit for your system.
Next, run the following in the terminals. 

##### Terminal 1

Run *jrt-controller*:
```sh
cd $JRTC_PATH/out/bin
./jrtc
```

##### Terminal 2

Run *srsRAN*: 
```sh
cd  $SRSRAN_DIR/build/apps/gnb
sudo ./gnb -c modified_conf_to_include_jbpf.yml
```

##### Terminal 3

Run the *jrt-controller* decoder (see [here](https://github.com/microsoft/jrt-controller/blob/main/docs/understand_advanced_app.md) for more info): 
```sh
cd $JRTC_PATH/sample_apps/advanced_example
./run_decoder.sh
```

##### Terminal 4

Run the *jbpf* reverse proxy (see [here](https://github.com/microsoft/jbpf/tree/main/examples/reverse_proxy) for more info):
```sh
sudo -E $SRSRAN_DIR/out/bin/srsran_reverse_proxy --host-port 30450 --address "/tmp/jbpf/jbpf_lcm_ipc"
```

##### Terminal 5

Load the *jbpf* codelets and *jrt-controller* apps for *srsRAN*:

First build the codelets:
```sh
cd $SRSRANAPP_DIR/codelets
./make.sh -o cleanall
./make.sh
```

Load and unload the [xran_packets](../jrtc_apps/xran_packets/) examples:
```sh
# load the xran_packets deployment
cd $JRTC_APPS
./load.sh -y $JRTC_APPS/xran_packets/deployment.yaml
# you should now see the decoder
./unload.sh -y $JRTC_APPS/xran_packets/deployment.yaml
```

Load and unload the [fapi](../jrtc_apps/fapi/) examples: 
```sh
# load the fapi deployment
cd $JRTC_APPS
./load.sh -y $JRTC_APPS/fapi/deployment.yaml
# you should now see the decoder
./unload.sh -y $JRTC_APPS/fapi/deployment.yaml
```
