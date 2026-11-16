/* Ring buffer for the offline samples (task 4.F3, FR-D04). Pure C. */
#include "nw_sample_ring.h"

void nw_ring_init(nw_ring_t *r)
{
    r->head = 0;
    r->count = 0;
    r->overwritten = 0;
}

bool nw_ring_push(nw_ring_t *r, const nw_sample_t *s)
{
    if (!r || !s) return false;
    bool lost = (r->count == NW_RING_CAP); /* full: head points at the oldest slot, which this write replaces */
    r->slot[r->head] = *s;
    r->head = (uint16_t)((r->head + 1) % NW_RING_CAP);
    if (lost) r->overwritten++;
    else r->count++;
    return lost;
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

size_t nw_ring_consume(nw_ring_t *r, size_t n)
{
    if (!r) return 0;
    if (n > r->count) n = r->count;
    r->count = (uint16_t)(r->count - n);
    return n;
}
