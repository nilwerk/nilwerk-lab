/* Host tests for the pure helpers of the boot-loop guard's ESP-IDF adapter (task 4.F7b): reset-reason mapping (header rule c) and the sleep-path
 * table (header rules a and b). No ESP-IDF. The numbers below are esp_reset_reason_t as in ESP-IDF 5.4 (esp_system.h); the adapter has a _Static_assert
 * for ESP_RST_POWERON, the other values here are the "must map to OTHER" cases. Every rule has a mutant in mutate_bootguard_map.py. */
#include <stdio.h>
#include "nwtest.h"
#include "nw_bootguard_map.h"

int nwtest_failed, nwtest_checked;

static void test_reset_reason_mapping(void)
{
    CHECK_EQ(NW_BG_IDF_RST_POWERON, 1);                         /* ESP_RST_POWERON */
    CHECK_EQ(nw_bg_map_reset_reason(1), NW_BG_RESET_POWERON);
    CHECK_EQ(NW_BG_RESET_OTHER, 0);                             /* the fail-safe value is 0 */
    CHECK_EQ(nw_bg_map_reset_reason(0), NW_BG_RESET_OTHER);     /* ESP_RST_UNKNOWN */
    for (int r = 2; r <= 15; r++)                               /* EXT, SW, PANIC, INT_WDT, TASK_WDT, WDT, DEEPSLEEP, BROWNOUT, SDIO, USB, JTAG, EFUSE, PWR_GLITCH, CPU_LOCKUP */
        CHECK_EQ(nw_bg_map_reset_reason(r), NW_BG_RESET_OTHER);
    CHECK_EQ(nw_bg_map_reset_reason(-1), NW_BG_RESET_OTHER);    /* a value this code has never seen */
    CHECK_EQ(nw_bg_map_reset_reason(1000), NW_BG_RESET_OTHER);
    CHECK_EQ(nw_bg_map_reset_reason(257), NW_BG_RESET_OTHER);   /* no truncation to the low byte */
}

static void test_sleep_path_table(void)
{
    /* rule (a): every deliberate sleep path confirms */
    CHECK(nw_bg_path_confirms(NW_BG_PATH_NORMAL_END));
    CHECK(nw_bg_path_confirms(NW_BG_PATH_LOW_BATTERY_SKIP));
    CHECK(nw_bg_path_confirms(NW_BG_PATH_BLE_SETUP_TIMEOUT));
    CHECK(nw_bg_path_confirms(NW_BG_PATH_BEFORE_OTA_REBOOT));
    /* rule (c) and the guard's own sleeps: no confirm */
    CHECK(!nw_bg_path_confirms(NW_BG_PATH_RESET_BUTTON));
    CHECK(!nw_bg_path_confirms(NW_BG_PATH_TOKEN_REVOKED_RESTART));
    CHECK(!nw_bg_path_confirms(NW_BG_PATH_FALLBACK_SLEEP));         /* confirming here would drop the probation boot */
    CHECK(!nw_bg_path_confirms(NW_BG_PATH_ROLLBACK_FAILED_SLEEP));  /* rule (b) */
    /* fail safe */
    CHECK(!nw_bg_path_confirms(NW_BG_PATH_COUNT));
    CHECK(!nw_bg_path_confirms((nw_bg_path_t)-1));
    CHECK(!nw_bg_path_confirms((nw_bg_path_t)99));
    CHECK_EQ(NW_BG_PATH_COUNT, 8);                                  /* a new path is a visible test edit: decide its confirm rule here */
}

int main(void)
{
    test_reset_reason_mapping();
    test_sleep_path_table();
    printf("test_bootguard_map: %d checks, %d failed\n", nwtest_checked, nwtest_failed);
    return nwtest_failed ? 1 : 0;
}
