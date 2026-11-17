// S02 Sign up / Sign in. Requirement: FR-A01 (e-mail + password account, optional display name stored in profiles.display_name).
import React, { useState } from 'react';
import { Button, Field, Notice, Screen } from '../ui/primitives';
import { t } from '../i18n';
import { useAuth } from '../auth/AuthContext';
import { AuthError } from '../auth/types';
import { validateDisplayName, validateEmail, validatePassword, type FieldResult } from '../validation';

export type AuthMode = 'signUp' | 'signIn';

const msg = (r: FieldResult) => (r ? t(r.key, r.params) : null);

export function errorKey(e: unknown): string {
  const code = e instanceof AuthError ? e.code : 'unknown';
  return { invalid_credentials: 'auth.error.invalidCredentials', email_taken: 'auth.error.emailTaken', network: 'auth.error.network', not_configured: 'auth.error.notConfigured', unauthorized: 'auth.error.unknown', server: 'auth.error.unknown', unknown: 'auth.error.unknown' }[code];
}

export function AuthFormScreen({ mode, onSwitch, onBack }: { mode: AuthMode; onSwitch: () => void; onBack: () => void }) {
  const { service } = useAuth();
  const up = mode === 'signUp';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [touched, setTouched] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmEmail, setConfirmEmail] = useState<string | null>(null);

  // Sign-in only checks "not empty"; the password length rule applies to new passwords.
  const eErr = touched ? msg(validateEmail(email)) : null;
  const pErr = touched ? (up ? msg(validatePassword(password)) : password ? null : t('validation.password.required')) : null;
  const nErr = up && touched ? msg(validateDisplayName(name)) : null;

  const submit = async () => {
    setTouched(true);
    setError(null);
    const bad = validateEmail(email) || (up ? validatePassword(password) : password ? null : { key: 'validation.password.required' }) || (up ? validateDisplayName(name) : null);
    if (bad) return;
    setBusy(true);
    try {
      if (up) {
        const r = await service.signUp(email, password, name);
        if (r.needsConfirmation) setConfirmEmail(email.trim());
      } else {
        await service.signIn(email, password);
      }
      // On success the session change moves the app to the profile screen (AuthProvider).
    } catch (e) {
      setError(t(errorKey(e)));
    } finally {
      setBusy(false);
    }
  };

  const title = t(up ? 'auth.signUp.title' : 'auth.signIn.title');
  return (
    <Screen title={title} onBack={onBack}>
      {confirmEmail ? <Notice kind="info" text={t('auth.signUp.checkEmail', { email: confirmEmail })} /> : null}
      {error ? <Notice kind="error" text={error} /> : null}
      <Field label={t('auth.email')} value={email} onChangeText={setEmail} error={eErr} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} autoComplete="email" textContentType="emailAddress" />
      <Field label={t('auth.password')} value={password} onChangeText={setPassword} error={pErr} secureTextEntry autoCapitalize="none" autoComplete={up ? 'new-password' : 'current-password'} textContentType={up ? 'newPassword' : 'password'} />
      {up ? <Field label={t('auth.displayName')} value={name} onChangeText={setName} error={nErr} autoComplete="name" textContentType="name" /> : null}
      <Button label={t(up ? 'auth.signUp.submit' : 'auth.signIn.submit')} onPress={submit} busy={busy} />
      <Button label={t(up ? 'auth.haveAccount' : 'auth.noAccount')} variant="ghost" onPress={onSwitch} />
    </Screen>
  );
}
