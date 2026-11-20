/* SIMULATOR ONLY (CONFIG_PLANT_SIM_MOCK_SENSORS). MOCKED sensor values for the QEMU boot test.
 * These numbers are fixed constants chosen for the test, NOT measurements. Every line this module prints starts with `NWSIMMOCK`.
 * Not used by any board build. See tests/qemu_boot_check.sh and sdkconfig.defaults.sim-qemu. */
#ifndef SIM_MOCK_HAL_H
#define SIM_MOCK_HAL_H

#include "nw_hal.h"

/* Fills *hal with the mock implementation (ctx unused). Returns 0. Prints the NWSIMMOCK banner. */
int nw_sim_mock_hal_init(nw_hal_t *hal);
/* Same role as nw_hal_esp32_prepare_deep_sleep() in the mock build: nothing to hold, the mock has no GPIO. */
void nw_sim_mock_prepare_deep_sleep(void);

#endif
