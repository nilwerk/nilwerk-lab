// Layout kit (src/ui/layout.tsx) used by every screen: back arrow and fixed header (48 px target, 3:1 control border), token-driven text,
// spacing, list rows, and clamped meters. Pure render tests with the real theme tokens (no network, no backend).
import React from 'react';
import { StyleSheet, Text } from 'react-native';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { Column, ListRow, Row, Type } from '../ui/kit';
import { BackButton, Screen } from '../ui/primitives';
import { getTheme, spacing, type as typeTokens, minTouchTarget } from '../../theme';
import { t } from '../i18n';

const light = getTheme('light');
const flat = (el: { props: { style?: unknown } }) => StyleSheet.flatten(el.props.style as never) as Record<string, unknown>;

describe('back control (48 px target, control contrast; the kit BackButton is used by the screen header)', () => {
  test('BackButton is a 48 by 48 px button named by the back label, and calls onPress', async () => {
    const onPress = jest.fn();
    await render(<BackButton onPress={onPress} />);
    const b = screen.getByRole('button', { name: t('a11y.back') });
    const s = flat(b);
    expect(s.width).toBe(minTouchTarget);
    expect(s.height).toBe(minTouchTarget);
    expect(s.borderColor).toBe(light.color.control);
    fireEvent.press(b);
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  test('the screen header shows the back control and not a "Back" text button', async () => {
    const onBack = jest.fn();
    await render(<Screen title="Plants" onBack={onBack}><Text>content</Text></Screen>);
    expect(screen.queryByText(t('common.back'))).toBeNull();
    fireEvent.press(screen.getByRole('button', { name: t('a11y.back') }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  test('a screen without onBack has no back control', async () => {
    await render(<Screen title="Welcome"><Text>content</Text></Screen>);
    expect(screen.queryByRole('button', { name: t('a11y.back') })).toBeNull();
  });
});

describe('text and spacing come from tokens', () => {
  test('Type takes the type token, the colour token, and the mono face on request', async () => {
    await render(<Type variant="h2" tone="muted" mono>Value</Type>);
    const s = flat(screen.getByText('Value'));
    expect(s.fontSize).toBe(typeTokens.h2.fontSize);
    expect(s.color).toBe(light.color.muted);
    expect(s.fontFamily).toBe(light.fontFamily.mono);
  });

  test('Type header marks a heading role; right and width are applied', async () => {
    await render(<Type variant="caption" header right width={56}>Head</Type>);
    expect(screen.getByRole('header')).toBeTruthy();
    const s = flat(screen.getByText('Head'));
    expect(s.textAlign).toBe('right');
    expect(s.width).toBe(56);
  });

  test('Stack and Row use the spacing token for the gap (default sm)', async () => {
    await render(<><Column testID="stack"><Text>a</Text></Column><Column testID="big" gap="lg"><Text>b</Text></Column><Row testID="row" wrap between><Text>c</Text></Row></>);
    expect(flat(screen.getByTestId('stack')).gap).toBe(spacing.sm);
    expect(flat(screen.getByTestId('big')).gap).toBe(spacing.lg);
    const row = flat(screen.getByTestId('row'));
    expect(row.flexWrap).toBe('wrap');
    expect(row.justifyContent).toBe('space-between');
  });
});

describe('list rows and meters', () => {
  test('ListRow has a hairline below unless it is the last row, and a 48 px minimum height', async () => {
    await render(<><ListRow testID="a"><Text>a</Text></ListRow><ListRow testID="z" last><Text>z</Text></ListRow></>);
    expect(flat(screen.getByTestId('a')).borderBottomWidth).toBe(1);
    expect(flat(screen.getByTestId('z')).borderBottomWidth).toBe(0);
    expect(flat(screen.getByTestId('a')).minHeight).toBe(minTouchTarget);
  });
});
