# Introduction

This project provides a collection of sample applications for instrumenting **srsRAN** using the  
[jbpf](https://github.com/microsoft/jbpf) and [jrt-controller](https://github.com/microsoft/jrt-controller) frameworks.

# Getting Started

The simplest way to get started is by using Kubernetes. This is the default installation method and helps eliminate any dependency-related issues.
However, we also support bare-metal installations.
For bare-metal setup instructions, please follow [these instructions](docs/baremetal.md) 

### Prerequisites

Before starting, ensure that **Kubernetes** and **Helm** are installed and configured. 
If you are not an expert in Kubernetes, you can try one of the simple, single-node setups, such as [k3d](https://k3s.io/). 
This guide assumes **srsRAN** will be deployed using **Helm**.

### Preparing the Environment

#### Initialize submodules:

```bash
cd ~/jbpf_apps
./init_submodules.sh
```

#### Set required environment variables:

```bash
source set_vars.sh
```

#### There are two ways to start the srsRAN deployment:
   - with JRTC - this will create pod, one for srsRAN, and one for JRTC.  The JRTC pod has two containers; one for the *jrt-controller* and one running the *jrt-decoder*.
   - without JRTC - This will just create a single pod, for srsRAN.

#### Start the srsRAN

Move to the ***jrtc-apps/containers/Helm*** directory and make sure that parameters `related to local setup, such as Core IP, RRH, Local MAC Address, and VLAN ID are correctly configured either in the values.yaml` or supplied via a separate YAML file. 

The easiest way to configure parameters related to local setup is to supply them via seperate yaml file - lets say config.yaml. Here is an example `config.yaml`. Please note that `config.yaml` will overwrite parameters in the `values.yaml` file.

  ```
  duConfigs:
    du1:
      cells:
        cell1:
          cellID: 1
          ruNAME: "RRH"
          ruLocalMAC: "00:11:22:33:0a:a6" 
          ruRemoteMAC: "6c:ad:ad:00:0a:a6"
          ruVLAN: "1"
          physicalCellID: 1

  cell_cfg:
    plmn: "00101"

  ngcParams:
    coreIP: 192.168.101.50 
    tac: "000001" 
    plmn: "00101" 
  ```


 Once the parameters are configured correctly we can deploy srsRAN

  
  `Deploy RAN without jrtc:`

  ```
  ./install.sh -h . -f config.yaml
  ```

  Expected output:

  ```bash
  kubectl get pods -n ran

  NAME            READY   STATUS    RESTARTS   AGE
  srs-gnb-du1-0   3/3     Running   0          11s
  ```

  `Deploy RAN with jrtc:`

  ```
  cd ~/jrtc-apps/containers/Helm
  ./install.sh -h . -f config.yaml -f jrtc.yaml
  ```
 
  Expected output:

  ```bash
  kubectl get pods -n ran

  NAME            READY   STATUS    RESTARTS   AGE
  jrtc-0          2/2     Running   0          11s
  srs-gnb-du1-0   3/3     Running   0          11s
  ```

---

## Running the Examples

This project includes two examples:

- [Example 1](./docs/example_no_jrtc.md):  
  Demonstrates data collection without using *jrt-controller*. Data is streamed to a local decoder and printed on-screen.

- [Example 2](./docs/example_w_jrtc.md):  
  Demonstrates data collection using *jrt-controller*.  Data is transferred from srsRAN to *jrt-controller* via shared memory.
   
---

# License

This project is licensed under the [MIT License](LICENSE.md).

---