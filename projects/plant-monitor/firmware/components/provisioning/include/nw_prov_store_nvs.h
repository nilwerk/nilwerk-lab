/* ESP-IDF NVS adapter for nw_prov_store_t (task 4.F2). Namespace "nw_prov", one versioned blob "rec".
 * A-013 / Q-H6: credentials live in the device NVS only, plain flash (no NVS encryption) for the demo. Not run on hardware. */
#ifndef NW_PROV_STORE_NVS_H
#define NW_PROV_STORE_NVS_H
#include "nw_prov.h"
/* Requires nvs_flash_init() to have been called. Fills `out` with load/save/erase bound to NVS (ctx unused). */
void nw_prov_store_nvs(nw_prov_store_t *out);
#endif
