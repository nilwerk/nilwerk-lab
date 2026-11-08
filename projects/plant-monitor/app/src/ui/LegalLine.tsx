// Privacy / Impressum line (A-052, approved by Arsany 2026-11-08).
// DRAFT: needs Arsany/legal review before store release. It states only the contact address and the fact that mail is processed by Google.
// It makes no other legal claim (no controller, no retention, no GDPR basis); do not add any without legal review.
import React from 'react';
import { Text } from 'react-native';
import { legalContact } from '../config';
import { t } from '../i18n';
import { useTheme } from './useTheme';

export function LegalLine({ contactEmail }: { contactEmail: string }) {
  const th = useTheme();
  return <Text accessibilityLabel={t('legal.contactLabel')} style={{ color: th.color.muted, ...th.type.caption }}>{t('legal.line', { email: legalContact(contactEmail) })}</Text>;
}
