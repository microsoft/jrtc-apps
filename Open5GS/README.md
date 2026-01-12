- [1. Introduction](#1-introduction)
- [2. Helper scripts](#2-helper-scripts)


# 1. Introduction

To use the [dashboard](../jrtc_apps/dashboard) application, subscriber information must be sent from the Core to the app.

MSR uses the [Open5GS core](https://github.com/open5gs/open5gs.git) for this purpose. This folder contains the Open5GS submodule pinned to the tested Git commit, along with the corresponding patch that must be applied so the Core AMF entity can forward subscriber information.


# 2. Helper scripts

To apply the patch:-
```bash
./apply_patch.sh
```

If you mqke updates to the core and need to generate a new patch file:-
```bash
./create_patch.sh
```
