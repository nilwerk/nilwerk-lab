// Shared screen kit (src/ui/kit.tsx): one set of components for every screen. Each test uses a hand-written value.
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { Card, Caption, BottomSheet, EmptyState, SectionTitle, StatusWord, ValueRow } from '../ui/kit';
import { contrast } from './contrastUtil';
import { colors, minTouchTarget } from '../../theme';
import { fakeDaily } from '../analytics/fakeAnalytics';

describe('Card, SectionTitle, Caption', () => {
  test('Card shows its children; SectionTitle is a header', async () => {
    await render(<Card><Caption>Soil</Caption><SectionTitle>Latest reading</SectionTitle></Card>);
    expect(screen.getByText('Soil')).toBeTruthy();
    expect(screen.getByRole('header', { name: 'Latest reading' })).toBeTruthy();
  });
});

describe('StatusWord and ValueRow', () => {
  test('Good and Low are the words, not colour alone', async () => {
    await render(<><StatusWord state="good" /><StatusWord state="low" /></>);
    expect(screen.getByText('Good')).toBeTruthy();
    expect(screen.getByText('Low')).toBeTruthy();
  });
  test('ValueRow shows the label, the value and the state word (hand-written: "Soil", "38 %", "Good")', async () => {
    await render(<ValueRow label="Soil" value="38 %" state="good" />);
    expect(screen.getByText('Soil')).toBeTruthy();
    expect(screen.getByText('38 %')).toBeTruthy();
    expect(screen.getByText('Good')).toBeTruthy();
  });
  test('ValueRow with no value and a state shows only the state word; with no value and no state, a dash', async () => {
    await render(<ValueRow label="Soil" value={null} state="low" />);
    expect(screen.getByText('Low')).toBeTruthy();
    expect(screen.queryByText('-')).toBeNull();
  });
  test('ValueRow with no value and no state shows the dash', async () => {
    await render(<ValueRow label="Light" value={null} />);
    expect(screen.getByText('-')).toBeTruthy();
  });
});

describe('EmptyState', () => {
  test('title, body, and one primary action that calls back once', async () => {
    const onAction = jest.fn();
    await render(<EmptyState title="No plants yet" body="Add your first sensor." action="Add your first plant" onAction={onAction} />);
    expect(screen.getByRole('header', { name: 'No plants yet' })).toBeTruthy();
    expect(screen.getByText('Add your first sensor.')).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: 'Add your first plant' }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });
  test('no action button when none is given', async () => {
    await render(<EmptyState title="No alerts" body="Nothing is open." />);
    expect(screen.queryByRole('button')).toBeNull();
  });
});

describe('BottomSheet', () => {
  test('shows its title and content; the Close button and the backdrop both call onClose', async () => {
    const onClose = jest.fn();
    await render(<BottomSheet visible title="Stats" closeLabel="Close" onClose={onClose}><Caption>Daily average</Caption></BottomSheet>);
    expect(screen.getByRole('header', { name: 'Stats' })).toBeTruthy();
    expect(screen.getByText('Daily average')).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: 'Close' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
  test('hidden sheet renders nothing of its content', async () => {
    await render(<BottomSheet visible={false} title="Stats" closeLabel="Close" onClose={() => undefined}><Caption>Hidden text</Caption></BottomSheet>);
    expect(screen.queryByText('Hidden text')).toBeNull();
  });
});

describe('kit colour and size rules (hand-written thresholds)', () => {
  test('control borders are 3:1 on bg and surface; targets are 48 px', () => {
    for (const bg of [colors.light.bg, colors.light.surface]) expect(contrast(colors.light.control, bg)).toBeGreaterThanOrEqual(3);
    expect(minTouchTarget).toBeGreaterThanOrEqual(48);
  });
  test('status words: Good (ok) and Low (low) reach 4.5:1 on the surface', () => {
    expect(contrast(colors.light.ok, colors.light.surface)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(colors.light.low, colors.light.surface)).toBeGreaterThanOrEqual(4.5);
  });
});

describe('mock analytics fixture (hand-computed gap)', () => {
  // window 30 ending 26 Nov 2026 (UTC): the days with i = 27, 18, 9, 0 days before the end are gaps.
  // Oldest first, index 2 is 27 days before the end = 30 Oct 2026, a gap.
  test('index 2 is 30 Oct 2026 and has no soil value; index 0 has one', async () => {
    const days = fakeDaily(30, new Date('2026-11-26T10:00:00Z'));
    expect(days).toHaveLength(30);
    expect(days[days.length - 1].date).toBe('2026-11-26');
    expect(days[2]).toMatchObject({ date: '2026-10-30', soilPctMean: null, readingCount: 0 });
    expect(days[0].soilPctMean).not.toBeNull();
  });
});
