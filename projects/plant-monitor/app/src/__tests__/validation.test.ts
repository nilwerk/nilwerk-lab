// FR-A01 form validation
import { validateEmail, validatePassword, validateDisplayName, validateDeleteConfirm, PASSWORD_MIN, DISPLAY_NAME_MAX } from '../validation';

describe('validation (FR-A01)', () => {
  test('email', () => {
    expect(validateEmail('')?.key).toBe('validation.email.required');
    expect(validateEmail('  ')?.key).toBe('validation.email.required');
    for (const bad of ['a', 'a@b', 'a b@c.de', '@c.de', 'a@.de']) expect(validateEmail(bad)?.key).toBe('validation.email.invalid');
    expect(validateEmail(' sam@example.com ')).toBeNull();
    expect(validateEmail('a'.repeat(250) + '@x.de')?.key).toBe('validation.email.invalid');
  });
  test('password', () => {
    expect(validatePassword('')?.key).toBe('validation.password.required');
    expect(validatePassword('x'.repeat(PASSWORD_MIN - 1))).toEqual({ key: 'validation.password.short', params: { min: PASSWORD_MIN } });
    expect(validatePassword('x'.repeat(PASSWORD_MIN))).toBeNull();
  });
  test('display name is optional, max length', () => {
    expect(validateDisplayName('')).toBeNull();
    expect(validateDisplayName('x'.repeat(DISPLAY_NAME_MAX))).toBeNull();
    expect(validateDisplayName('x'.repeat(DISPLAY_NAME_MAX + 1))?.key).toBe('validation.displayName.long');
  });
  test('delete confirmation needs exactly DELETE', () => {
    expect(validateDeleteConfirm('DELETE')).toBeNull();
    expect(validateDeleteConfirm(' DELETE ')).toBeNull();
    for (const bad of ['', 'delete', 'DELET', 'DELETE!']) expect(validateDeleteConfirm(bad)?.key).toBe('validation.delete.mismatch');
  });
});
