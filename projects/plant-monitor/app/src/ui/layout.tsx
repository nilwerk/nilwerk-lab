// Brand asset block (Welcome only). The other layout blocks moved to ui/kit.tsx on review.
import React from 'react';
import { Image, View, type ImageSourcePropType } from 'react-native';
import { useTheme } from './useTheme';

/** The app logo, centred, at a fixed size with the theme radius. The label is the screen-reader name. */
export function Logo({ source, label }: { source: ImageSourcePropType; label: string }) {
  const th = useTheme();
  return (
    <View style={{ alignItems: 'center' }}>
      <Image source={source} accessibilityLabel={label} style={{ width: LOGO_SIZE, height: LOGO_SIZE, borderRadius: th.radius.lg }} />
    </View>
  );
}
const LOGO_SIZE = 96;
