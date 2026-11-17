# BLE contract: SRP user name, nw-claim order, NVS keys

**What it shows:** the setup contract now names the SRP6a user name (`wifiprov`), the real step order (`nw-claim` any time after the handshake, `prov-config` + apply) and the NVS namespaces and keys the firmware uses. Five traceability rows and ADR-016 (A-105..A-107) were added.
**Evidence:** `python3 projects/plant-monitor/firmware/test/host/check_prov_contract.py` prints "0 failed"; the NVS names are quoted from `nw_prov_store_nvs.c` and `nw_prov_idf.c`. Documents only, no hardware.
**Not verified:** the user name is not set in our firmware code (ESP-IDF default assumed); the factory tool does not exist yet.
