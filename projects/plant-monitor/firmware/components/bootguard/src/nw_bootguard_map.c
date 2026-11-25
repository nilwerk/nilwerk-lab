/* Pure helpers for the boot-loop guard's ESP-IDF adapter. See nw_bootguard_map.h. */
#include "nw_bootguard_map.h"

nw_bg_reset_t nw_bg_map_reset_reason(int idf_reason)
{
    return idf_reason == NW_BG_IDF_RST_POWERON ? NW_BG_RESET_POWERON : NW_BG_RESET_OTHER;
}

bool nw_bg_path_confirms(nw_bg_path_t path)
{
    switch (path) {
    case NW_BG_PATH_NORMAL_END:
    case NW_BG_PATH_LOW_BATTERY_SKIP:
    case NW_BG_PATH_BLE_SETUP_TIMEOUT:
    case NW_BG_PATH_BEFORE_OTA_REBOOT:
        return true;
    case NW_BG_PATH_RESET_BUTTON:
    case NW_BG_PATH_TOKEN_REVOKED_RESTART:
    case NW_BG_PATH_FALLBACK_SLEEP:
    case NW_BG_PATH_ROLLBACK_FAILED_SLEEP:
    case NW_BG_PATH_COUNT:
    default:
        return false;
    }
}
