// S40 Premium sheet. Requirement: FR-P04 (premium is a server flag; no in-app purchase in v1, A-024: "activated by Nilwerk" + contact link).
import React from 'react';
import { Linking } from 'react-native';
import { Body, Button, Screen } from '../ui/primitives';
import { Caption, Column } from '../ui/kit';
import { LegalLine } from '../ui/LegalLine';
import { t } from '../i18n';

export function contactUrl(email: string): string | null {
  return email ? `mailto:${email}?subject=${encodeURIComponent(t('premium.contactSubject'))}` : null;
}

export function PremiumScreen({ contactEmail, onBack }: { contactEmail: string; onBack: () => void }) {
  const url = contactUrl(contactEmail);
  return (
    <Screen title={t('premium.title')} onBack={onBack}>
      <Body>{t('premium.body')}</Body>
      <Body>{t('premium.activatedByNilwerk')}</Body>
      {/* full comparison: shown here only, opened from Profile with What is Premium? */}
      <Column gap="xs" accessibilityLabel={t('profile.price.heading')}>
        <Caption>{t('profile.price.free')}</Caption>
        <Caption>{t('profile.price.premium')}</Caption>
      </Column>
      {url ? <Button label={t('premium.contactUs')} onPress={() => { Linking.openURL(url).catch(() => undefined); }} /> : <Body muted>{t('premium.noContact')}</Body>}
      <LegalLine contactEmail={contactEmail} />
    </Screen>
  );
}
