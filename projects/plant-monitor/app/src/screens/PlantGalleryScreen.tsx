// S23 Photo gallery. Requirements: FR-A05 (unlimited photos per plant, each with its date, sorted newest or oldest first), FR-A04 (metadata shown: location type, room, soil type), NFR-06 (own rows only under RLS).
// No limit on the number of photos: every photo is rendered (plain map, no windowed list, so the test with 60 photos sees all of them).
// Not in this slice: upload ("+ Add", 4.A3 camera/library), full-screen view, long-press delete, signed image URLs (the mock has no image bytes).
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Text, View } from 'react-native';
import { Body, Button, Notice, Screen } from '../ui/primitives';
import { PlantMeta } from '../ui/PlantMeta';
import { useTheme } from '../ui/useTheme';
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
  const th = useTheme();
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
        <View style={{ gap: th.spacing.sm }}>
          <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h3 }}>{t('gallery.empty.title')}</Text>
          <Body muted>{t('gallery.empty.body')}</Body>
        </View>
      ) : null}
      {photos && photos.length > 0 ? (
        <>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: th.spacing.sm, alignItems: 'center' }}>
            <Text testID="gallery-count" style={{ color: th.color.muted, ...th.type.caption, flexGrow: 1 }}>{t('gallery.count', { n: photos.length })}</Text>
            <Button label={t('gallery.sortNewest')} variant={order === 'newest' ? 'secondary' : 'ghost'} onPress={() => setOrder('newest')} />
            <Button label={t('gallery.sortOldest')} variant={order === 'oldest' ? 'secondary' : 'ghost'} onPress={() => setOrder('oldest')} />
          </View>
          {/* #238 decision: grid of three per row, grouped under a header per day (the order follows the sort) */}
          {dayGroups(sorted).map((g) => (
            <View key={g.day} testID="gallery-day" style={{ gap: th.spacing.sm }}>
              <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.bodyStrong }}>{g.day}</Text>
              <View testID="gallery-grid" style={{ flexDirection: 'row', flexWrap: 'wrap', gap: th.spacing.sm }}>
                {g.photos.map((ph) => (
                  <View key={ph.id} testID="gallery-photo" accessible accessibilityLabel={t('gallery.photoA11y', { date: g.day })}
                    style={{ flexBasis: '30%', flexGrow: 0, flexShrink: 0, gap: th.spacing.xs }}>
                    <View style={{ aspectRatio: 1, borderRadius: th.radius.md, borderWidth: 1, borderColor: th.color.line, backgroundColor: th.color.surface, alignItems: 'center', justifyContent: 'center' }}>
                      <Text style={{ color: th.color.muted, ...th.type.caption }}>{g.day}</Text>
                    </View>
                  </View>
                ))}
              </View>
            </View>
          ))}
        </>
      ) : null}
    </Screen>
  );
}
