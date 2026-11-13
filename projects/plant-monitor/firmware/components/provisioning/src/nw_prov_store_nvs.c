/* NVS adapter (task 4.F2, FR-D03, A-013). ESP-IDF only; not built on the host. UNVERIFIED on hardware. */
#include "nw_prov_store_nvs.h"

#include <string.h>

#include "nvs.h"

#define NS "nw_prov"
#define KEY "rec"
#define REC_VERSION 1

typedef struct { uint32_t version; nw_prov_record_t rec; } blob_t;   /* blob size = 4 + sizeof(record); a size mismatch counts as "nothing stored" */

static int load(void *ctx, nw_prov_record_t *out)
{
    (void)ctx;
    nvs_handle_t h;
    esp_err_t e = nvs_open(NS, NVS_READONLY, &h);
    if (e == ESP_ERR_NVS_NOT_FOUND) return 1;
    if (e != ESP_OK) return -1;
    blob_t b; size_t n = sizeof b;
    e = nvs_get_blob(h, KEY, &b, &n);
    nvs_close(h);
    if (e == ESP_ERR_NVS_NOT_FOUND) return 1;
    if (e != ESP_OK) return -1;
    if (n != sizeof b || b.version != REC_VERSION) return 1;
    *out = b.rec;
    memset(&b, 0, sizeof b);
    return 0;
}

static int save(void *ctx, const nw_prov_record_t *rec)
{
    (void)ctx;
    nvs_handle_t h;
    if (nvs_open(NS, NVS_READWRITE, &h) != ESP_OK) return -1;
    blob_t b = {.version = REC_VERSION, .rec = *rec};
    esp_err_t e = nvs_set_blob(h, KEY, &b, sizeof b);
    if (e == ESP_OK) e = nvs_commit(h);
    nvs_close(h);
    memset(&b, 0, sizeof b);
    return e == ESP_OK ? 0 : -1;
}

static int erase(void *ctx)
{
    (void)ctx;
    nvs_handle_t h;
    esp_err_t e = nvs_open(NS, NVS_READWRITE, &h);
    if (e != ESP_OK) return -1;
    e = nvs_erase_key(h, KEY);
    if (e == ESP_ERR_NVS_NOT_FOUND) e = ESP_OK;
    if (e == ESP_OK) e = nvs_commit(h);
    nvs_close(h);
    return e == ESP_OK ? 0 : -1;
}

void nw_prov_store_nvs(nw_prov_store_t *out)
{
    out->load = load;
    out->save = save;
    out->erase = erase;
}
