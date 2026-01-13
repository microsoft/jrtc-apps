
# 1. Preparation

To build required imagesm run in the project root:
```sh
./init_submodules.sh
```

This will initialise all submodules.

__Note that for the Docker/srsRAN_apps submodule, it is also patched with all files from folder "Docker/for_srsRAN_apps"__.


# 2. Build images

To build required images:
```sh
./init_submodules.sh
cd containers/Docker
sudo ./build_base.sh [-b <base-image-tag>]
sudo ./build_srs_jbpf.sh [-b <base-image-tag>] [-s <srs-image-tag>] [-c]   # Use -c for '--no-cache'
sudo ./build_srs_jbpf_sdk.sh [-s <srs-image-tag>]
sudo ./build_srs_jbpf_zmq.sh [-b <base-image-tag>] [-s <srs-image-tag>]
sudo ./build_srs_ue_base.sh [-b <base-image-tag>] [-s <srs-image-tag>] [-c]   # Use -c for '--no-cache'
sudo ./build_srs_ue.sh [-s <srs-image-tag>] [-c]   # Use -c for '--no-cache'

```
