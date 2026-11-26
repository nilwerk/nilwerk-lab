// S23 Photo gallery. Requirements: FR-A05 (unlimited photos per plant, each with its date, sorted newest or oldest first), FR-A04 (metadata shown: location type, room, soil type), NFR-06 (own rows only under RLS).
// No limit on the number of photos: every photo is rendered (plain map, no windowed list, so the test with 60 photos sees all of them).
// Not in this slice: upload ("+ Add", 4.A3 camera/library), full-screen view, long-press delete, signed image URLs (the mock has no image bytes).
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Body, Button, Notice, Screen } from '../ui/primitives';
import { PlantMeta } from '../ui/PlantMeta';
import { Caption, EmptyState, SectionTitle } from '../ui/kit';
import { Frame, GridCell, Row, Stack, Type } from '../ui/layout';
import { t } from '../i18n';
import { usePlants } from '../plants/PlantsContext';
import { fmtDay } from '../plants/format';
import { PlantsError, type PlantPhoto, type PlantSummary } from '../plants/types';

export type PhotoOrder = 'newest' | 'oldest';

/** Sorted copy by takenAt (ISO strings compare by time when parsed). */
export function sortPhotos(photos: PlantPhoto[], order: PhotoOrder): PlantPhoto[] {
  const dir = order === 'newest' ? -1 : 1;
  return [...photos].sort((a, b) => dir * (Date.parse(a.takenAt) - Date.parse(b.takenAt)));
}

/** Photos (already sorted) grouped by their day, keeping the order of the sort. */
export function dayGroups(photos: PlantPhoto[]): Array<{ day: string; photos: PlantPhoto[] }> {
  const out: Array<{ day: string; photos: PlantPhoto[] }> = [];
  for (const ph of photos) {
    const day = fmtDay(ph.takenAt);
    const last = out[out.length - 1];
    if (last && last.day === day) last.photos.push(ph); else out.push({ day, photos: [ph] });
  }
  return out;
}

export function PlantGalleryScreen({ plant, onBack }: { plant: PlantSummary; onBack: () => void }) {
  const svc = usePlants();
  const [photos, setPhotos] = useState<PlantPhoto[] | null>(null);
  const [order, setOrder] = useState<PhotoOrder>('newest');
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try { setPhotos(await svc.listPhotos(plant.id)); }
    catch (e) { setError(t(e instanceof PlantsError && e.code === 'not_found' ? 'plant.error.notFound' : 'gallery.error')); }
  }, [svc, plant.id]);
  useEffect(() => { load(); }, [load]);

  const sorted = useMemo(() => (photos ? sortPhotos(photos, order) : []), [photos, order]);

  return (
    <Screen title={t('gallery.title', { plantName: plant.name })} onBack={onBack}>
      <PlantMeta plant={plant} />
      {error ? <Notice kind="error" text={error} /> : null}
      {error ? <Button label={t('common.tryAgain')} variant="secondary" onPress={load} /> : null}
      {photos === null && !error ? <Body muted>{t('common.loading')}</Body> : null}
      {photos && photos.length === 0 ? (
        <EmptyState title={t('gallery.empty.title')} body={t('gallery.empty.body')} />
      ) : null}
      {photos && photos.length > 0 ? (
        <>
          <Row wrap>
            <Type testID="gallery-count" tone="muted" variant="caption" flex>{t('gallery.count', { n: photos.length })}</Type>
            <Button label={t('gallery.sortNewest')} variant={order === 'newest' ? 'secondary' : 'ghost'} onPress={() => setOrder('newest')} />
            <Button label={t('gallery.sortOldest')} variant={order === 'oldest' ? 'secondary' : 'ghost'} onPress={() => setOrder('oldest')} />
          </Row>
          {/* #238 decision: grid of three per row, grouped under a header per day (the order follows the sort) */}
          {dayGroups(sorted).map((g) => (
            <Stack key={g.day} testID="gallery-day">
              <SectionTitle>{g.day}</SectionTitle>
              <Row wrap testID="gallery-grid">
                {g.photos.map((ph) => (
                  <GridCell key={ph.id} testID="gallery-photo" accessibilityLabel={t('gallery.photoA11y', { date: g.day })}>
                    <Frame><Caption>{g.day}</Caption></Frame>
                  </GridCell>
                ))}
              </Row>
            </Stack>
          ))}
        </>
      ) : null}
    </Screen>
  );
}
