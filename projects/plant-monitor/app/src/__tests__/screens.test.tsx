// Screen render + flow tests against the in-memory Supabase mock (FR-A01). Not a real backend.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { Root } from '../../App';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { t } from '../i18n';
import { createFakeSetup } from '../provisioning/fakeProvisioning';
import { SCREEN_FR } from '../ui/frIds';
import { SafeAreaProvider } from "react-native-safe-area-context";
import fs from 'fs';
import path from 'path';

const mount = async (service = createFakeAuth(), contactEmail = 'hello@example.invalid') => {
  await render(<SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } }}><AuthProvider service={service}><Root contactEmail={contactEmail} setup={createFakeSetup().services} /></AuthProvider></SafeAreaProvider>);
  return service;
};
const type = async (label: string, text: string) => fireEvent.changeText(await screen.findByLabelText(label), text);
const tap = async (label: string) => fireEvent.press(await screen.findByRole('button', { name: label }));

describe('signed-out flow', () => {
  test('welcome shows name, tagline and both entry buttons', async () => {
    await mount();
    expect(await screen.findByText('Know when your plants are thirsty. Set up a sensor in under 3 minutes.')).toBeTruthy();
    expect(screen.getByRole('header', { name: 'Plant Monitor' })).toBeTruthy();
    expect(screen.getByLabelText('Plant Monitor logo')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Create account' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'I already have an account' })).toBeTruthy();
  });

  test('sign up validates, then lands on the profile', async () => {
    const svc = await mount();
    await tap('Create account');
    await tap('Create account'); // submit empty
    expect(await screen.findByText('Enter your e-mail.')).toBeTruthy();
    expect(screen.getByText('Enter a password.')).toBeTruthy();
    await type('E-mail', 'sam@example.com');
    await type('Password', 'short');
    await tap('Create account');
    expect(await screen.findByText('Use at least 8 characters.')).toBeTruthy();
    await type('Password', 'long-enough-1');
    await type('Display name (optional)', 'Sam');
    await tap('Create account');
    expect(await screen.findByRole('header', { name: 'Profile' })).toBeTruthy();
    expect(svc.accounts[0].profile.displayName).toBe('Sam');
    expect(await screen.findByText('sam@example.com')).toBeTruthy();
    expect(await screen.findByText('Free')).toBeTruthy();
  });

  test('sign up with e-mail confirmation shows the check-your-e-mail notice', async () => {
    await mount(createFakeAuth({ needsConfirmation: true }));
    await tap('Create account');
    await type('E-mail', 'sam@example.com');
    await type('Password', 'long-enough-1');
    await tap('Create account');
    expect(await screen.findByText(/We sent a confirmation link to sam@example.com/)).toBeTruthy();
  });

  test('wrong password shows a plain error and stays on sign in', async () => {
    const svc = createFakeAuth();
    await svc.signUp('sam@example.com', 'long-enough-1');
    await svc.signOut();
    await mount(svc);
    await tap('I already have an account');
    await type('E-mail', 'sam@example.com');
    await type('Password', 'nope');
    await tap('Sign in');
    expect(await screen.findByText('E-mail or password is not right.')).toBeTruthy();
    await type('Password', 'long-enough-1');
    await tap('Sign in');
    expect(await screen.findByRole('header', { name: 'Profile' })).toBeTruthy();
  });
});

describe('signed-in flow', () => {
  const signedIn = async () => {
    const svc = createFakeAuth();
    await svc.signUp('sam@example.com', 'long-enough-1', 'Sam');
    await mount(svc);
    await screen.findByRole('header', { name: 'Profile' });
    return svc;
  };

  test('profile edit saves the name; sign out returns to welcome', async () => {
    const svc = await signedIn();
    await waitFor(() => expect(screen.getByLabelText('Display name').props.value).toBe('Sam'));
    await type('Display name', 'Samira');
    await tap('Save name');
    expect(await screen.findByText('Name saved.')).toBeTruthy();
    expect(svc.accounts[0].profile.displayName).toBe('Samira');
    await tap('Sign out');
    expect(await screen.findByRole('header', { name: 'Plant Monitor' })).toBeTruthy();
  });

  test('premium sheet says activated by Nilwerk and offers the contact link', async () => {
    await signedIn();
    await tap('What is Premium?');
    expect(await screen.findByText(/activated by Nilwerk/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Contact us' })).toBeTruthy();
  });

  test('delete account needs the word DELETE, then removes the account and returns to welcome', async () => {
    const svc = await signedIn();
    await tap('Delete account');
    expect(await screen.findByRole('header', { name: 'Delete account?' })).toBeTruthy();
    const del = screen.getByRole('button', { name: 'Delete everything' });
    expect(del.props.accessibilityState?.disabled ?? del.props['aria-disabled']).toBeTruthy();
    await type('Type DELETE to confirm', 'delete');
    expect(screen.getByRole('button', { name: 'Delete everything' }).props.accessibilityState?.disabled).toBe(true);
    await type('Type DELETE to confirm', 'DELETE');
    await tap('Delete everything');
    expect(await screen.findByRole('header', { name: 'Plant Monitor' })).toBeTruthy();
    expect(svc.accounts).toHaveLength(0);
  });

  test('failed delete keeps the account and says so', async () => {
    const svc = await signedIn();
    svc.options.deleteFails = true;
    await tap('Delete account');
    await type('Type DELETE to confirm', 'DELETE');
    await tap('Delete everything');
    expect(await screen.findByText(/Nothing was removed/)).toBeTruthy();
    expect(svc.accounts).toHaveLength(1);
  });
});

describe('legal line (A-052, draft)', () => {
  const LINE = 'Contact and privacy: hello@example.invalid. E-mail is processed by Google (Gmail).';
  test('welcome, profile and premium all show contact + Google processor', async () => {
    const svc = createFakeAuth();
    await svc.signUp('sam@example.com', 'long-enough-1', 'Sam');
    await svc.signOut();
    await mount(svc);
    expect(await screen.findByText(LINE)).toBeTruthy();
    await tap('I already have an account');
    await type('E-mail', 'sam@example.com');
    await type('Password', 'long-enough-1');
    await tap('Sign in');
    await screen.findByRole('header', { name: 'Profile' });
    expect(await screen.findByText(LINE)).toBeTruthy();
    await tap('What is Premium?');
    expect(await screen.findByText(LINE)).toBeTruthy();
  });
  test('an empty CONTACT_EMAIL hides the Premium link but the legal line keeps the default contact', async () => {
    await mount(createFakeAuth(), '');
    expect(await screen.findByText(/nilwerk\.team@gmail\.com\. E-mail is processed by Google/)).toBeTruthy();
  });
  test('the line makes no claim beyond contact and processor', () => {
    expect(t('legal.line', { email: 'x@y.z' })).toBe('Contact and privacy: x@y.z. E-mail is processed by Google (Gmail).');
  });
  test('source is marked as a draft for review', () => {
    const src = fs.readFileSync(path.resolve(__dirname, '../ui/LegalLine.tsx'), 'utf8');
    expect(src).toMatch(/DRAFT.*needs Arsany\/legal review/);
  });
});

describe('requirement citations', () => {
  test('every screen has FR ids in the map and in its source header', () => {
    const files: Record<keyof typeof SCREEN_FR, string> = {
      welcome: 'WelcomeScreen', signUp: 'AuthFormScreen', signIn: 'AuthFormScreen', profile: 'ProfileScreen', deleteAccount: 'DeleteAccountScreen', premium: 'PremiumScreen', setup: 'setup/SetupSteps',
    };
    for (const [screenName, ids] of Object.entries(SCREEN_FR)) {
      expect(ids.length).toBeGreaterThan(0);
      const src = fs.readFileSync(path.resolve(__dirname, '../screens', `${files[screenName as keyof typeof SCREEN_FR]}.tsx`), 'utf8');
      const header = src.split('\n').slice(0, 4).join('\n');
      for (const id of ids) expect(header).toContain(id);
    }
  });
});
