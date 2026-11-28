// S01 Welcome. Requirement: FR-A01 (account creation entry point). A-024: name "Plant Monitor", English only.
import React from 'react';
import { Button, Screen, Body } from '../ui/primitives';
import { Caption } from '../ui/kit';
import { Logo } from '../ui/layout';
import { LegalLine } from '../ui/LegalLine';
import { t } from '../i18n';

const WELCOME_LOGO_SIZE = 180;

export function WelcomeScreen({ onCreate, onSignIn, contactEmail }: { onCreate: () => void; onSignIn: () => void; contactEmail: string }) {
  return (
    <Screen title={t('app.name')}>
      {/* hero size on the first screen (owner feedback: the logo read too small at 96 px); fits a 360 px phone, the screen scrolls vertically */}
      <Logo source={require('../../assets/icon-1024.png')} label={t('a11y.logo')} size={WELCOME_LOGO_SIZE} />
      <Body>{t('welcome.tagline')}</Body>
      <Button label={t('welcome.createAccount')} onPress={onCreate} />
      <Button label={t('welcome.haveAccount')} variant="secondary" onPress={onSignIn} />
      <Caption>{t('welcome.privacy')}</Caption>
      <LegalLine contactEmail={contactEmail} />
    </Screen>
  );
}
