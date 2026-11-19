/* Ring buffer for the offline samples (task 4.F3, FR-D04). Pure C. Review fixes C1 (seq-based ack) and C2 (admission). */
#include "nw_sample_ring.h"

void nw_ring_init(nw_ring_t *r)
{
    r->head = 0;
    r->count = 0;
    r->next_seq = 0;
    r->overwritten = 0;
    r->rejected = 0;
}

static bool sample_ok(const nw_sample_t *s)
{
    if (s->ts < NW_TS_MIN) return false;                               /* unsynced RTC or schema minimum */
    if (s->present & (uint8_t)~NW_PRESENT_MASK) return false;
    if ((s->present & NW_HAS_MOISTURE) && s->moisture_x10 > 1000) return false;
    if ((s->present & NW_HAS_MOISTURE_RAW) && s->moisture_raw > 4095) return false;
    if ((s->present & NW_HAS_RH) && (s->rh_x100 < 0 || s->rh_x100 > 10000)) return false;
    return true;
}

nw_push_t nw_ring_push(nw_ring_t *r, const nw_sample_t *s, bool time_synced)
{
    if (!r || !s) return NW_PUSH_REJECTED_INVALID;
    if (!time_synced) { r->rejected++; return NW_PUSH_REJECTED_UNSYNCED; }
    if (!sample_ok(s)) { r->rejected++; return NW_PUSH_REJECTED_INVALID; }

    bool lost = (r->count == NW_RING_CAP); /* full: head points at the oldest slot, which this write replaces */
    nw_sample_t *slot = &r->slot[r->head];
    *slot = *s;
    slot->seq = ++r->next_seq;
    r->head = (uint16_t)((r->head + 1) % NW_RING_CAP);
    if (lost) {
        r->overwritten++;
        return NW_PUSH_STORED_OVERWROTE;
    }
    r->count++;
    return NW_PUSH_STORED;
}

size_t nw_ring_count(const nw_ring_t *r)
{
    return r ? r->count : 0;
}

const nw_sample_t *nw_ring_at(const nw_ring_t *r, size_t i)
{
    if (!r || i >= r->count) return NULL;
    size_t idx = ((size_t)r->head + NW_RING_CAP - r->count + i) % NW_RING_CAP;
    return &r->slot[idx];
}

const nw_sample_t *nw_ring_newest(const nw_ring_t *r)
{
    if (!r || r->count == 0) return NULL;
    return &r->slot[(r->head + NW_RING_CAP - 1) % NW_RING_CAP];
}

size_t nw_ring_consume_upto(nw_ring_t *r, uint32_t last_seq)
{
    size_t removed = 0;
    while (r && r->count > 0) {
        size_t oldest = ((size_t)r->head + NW_RING_CAP - r->count) % NW_RING_CAP;
        if (r->slot[oldest].seq > last_seq) break;   /* sent-batch samples are a prefix: stop at the first newer one */
        r->count--;
        removed++;
    }
    return removed;
}

bool nw_ring_valid(const nw_ring_t *r)
{
    if (!r || r->head >= NW_RING_CAP || r->count > NW_RING_CAP) return false;
    if (r->count == 0) return true;
    uint32_t prev = 0;
    for (size_t i = 0; i < r->count; i++) {
        const nw_sample_t *s = nw_ring_at(r, i);
        if (!sample_ok(s)) return false;
        if (i > 0 && s->seq <= prev) return false;
        if (s->seq == 0) return false;
        prev = s->seq;
    }
    return prev == r->next_seq;
}
