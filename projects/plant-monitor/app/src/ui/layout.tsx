// Brand asset block (Welcome only). The other layout blocks moved to ui/kit.tsx on review.
import React from 'react';
import { Image, View, type ImageSourcePropType } from 'react-native';
import { useTheme } from './useTheme';

/** The app logo, centred, with the theme radius. size is a square edge in px (default 96). The label is the screen-reader name. */
export const LOGO_SIZE = 96;
export function Logo({ source, label, size = LOGO_SIZE }: { source: ImageSourcePropType; label: string; size?: number }) {
  const th = useTheme();
  return (
    <View style={{ alignItems: 'center' }}>
      <Image source={source} accessibilityLabel={label} style={{ width: size, height: size, borderRadius: th.radius.lg }} />
    </View>
  );
}
