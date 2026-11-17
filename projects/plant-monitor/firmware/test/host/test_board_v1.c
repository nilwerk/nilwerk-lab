/* Host test: board.h with CONFIG_PLANT_BOARD_V1_SUPERMINI (task 4.F1 v1 bench, FR-D01).
 * Pin numbers are the ones in v1/WIRING.md section 3; check_board_v1.py proves board.h and that table agree, this file proves the
 * macros the firmware actually uses (soil analog on, divider 100k/100k, ADC channels follow the pins). No hardware involved. */
#define CONFIG_PLANT_BOARD_V1_SUPERMINI 1
#include <stdio.h>
#include <string.h>
#include "../../main/board.h"

_Static_assert(NW_PIN_BAT_SENS == 0, "WIRING.md section 3: GPIO0 BAT_SENS");
_Static_assert(NW_PIN_SOIL_PWR == 3, "WIRING.md section 3: GPIO3 SOIL_PWR");
_Static_assert(NW_PIN_SOIL_OUT == 4, "WIRING.md section 3: GPIO4 SOIL_OUT");
_Static_assert(NW_PIN_I2C_SDA == 6, "WIRING.md section 3: GPIO6 I2C_SDA (NOT the SuperMini Arduino default GPIO8)");
_Static_assert(NW_PIN_I2C_SCL == 7, "WIRING.md section 3: GPIO7 I2C_SCL (NOT the SuperMini Arduino default GPIO9)");
_Static_assert(NW_PIN_BUTTON == 9, "WIRING.md section 3: GPIO9 BOOT key");
_Static_assert(NW_ADC1_CH_BAT == 0 && NW_ADC1_CH_SOIL == 4, "ADC1 channels = GPIO numbers 0..4 on the ESP32-C3");
_Static_assert(NW_SOIL_ANALOG == 1, "v1 reads the analog probe (WIRING.md section 4.5)");
_Static_assert(NW_BAT_R_TOP_OHM == 100000u && NW_BAT_R_BOT_OHM == 100000u, "WIRING.md section 4.2: R1 = R2 = 100 kOhm");
_Static_assert(NW_I2C_HZ == 100000, "WIRING.md section 4.3: 100 kHz");

static int fails;
#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #c); fails++; } } while (0)

int main(void)
{
    CHECK(strcmp(NW_BOARD_NAME, "v1_supermini") == 0);
    /* nothing may drive GPIO1, GPIO2, GPIO8 (strap pins / unused in v1, WIRING.md section 3) */
    int used[] = {NW_PIN_BAT_SENS, NW_PIN_SOIL_PWR, NW_PIN_SOIL_OUT, NW_PIN_I2C_SDA, NW_PIN_I2C_SCL, NW_PIN_BUTTON};
    for (unsigned i = 0; i < sizeof used / sizeof used[0]; i++) {
        CHECK(used[i] != 1 && used[i] != 2 && used[i] != 8);
        for (unsigned j = i + 1; j < sizeof used / sizeof used[0]; j++) CHECK(used[i] != used[j]);
    }
    /* divider midpoint = V_bat / 2 so 4.2 V stays at 2.1 V (WIRING.md section 4.5) */
    CHECK(NW_BAT_R_TOP_OHM == NW_BAT_R_BOT_OHM);
    puts(fails ? "board v1: FAILED" : "board v1: all checks passed");
    return fails ? 1 : 0;
}
