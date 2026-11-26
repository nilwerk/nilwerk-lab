// S01 Welcome. Requirement: FR-A01 (account creation entry point). A-024: name "Plant Monitor", English only.
import React from 'react';
import { Image, Text, View } from 'react-native';
import { Button, Screen, Body } from '../ui/primitives';
import { Caption } from '../ui/kit';
import { useTheme } from '../ui/useTheme';
import { LegalLine } from '../ui/LegalLine';
import { t } from '../i18n';

export function WelcomeScreen({ onCreate, onSignIn, contactEmail }: { onCreate: () => void; onSignIn: () => void; contactEmail: string }) {
  const th = useTheme();
  return (
    <Screen title={t('app.name')}>
      <View style={{ alignItems: 'center' }}>
        <Image source={require('../../assets/icon-1024.png')} style={{ width: 96, height: 96, borderRadius: th.radius.lg }} accessibilityLabel={t('a11y.logo')} />
      </View>
      <Body>{t('welcome.tagline')}</Body>
      <Button label={t('welcome.createAccount')} onPress={onCreate} />
      <Button label={t('welcome.haveAccount')} variant="secondary" onPress={onSignIn} />
      <Caption>{t('welcome.privacy')}</Caption>
      <LegalLine contactEmail={contactEmail} />
    </Screen>
  );
}
