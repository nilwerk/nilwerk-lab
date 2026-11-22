'use strict';
// Minimal W3C WebDriver client for an Appium 2.x server, on Node's built-in fetch.
// No npm packages: the bench Pi needs only Node 20 and Appium 2.x.
// Error messages carry the method, path and WebDriver error name only, never a request body.

const ELEMENT_KEY = 'element-6066-11e4-a52e-4f735466cecf';

class Appium {
  constructor(baseUrl) {
    this.base = baseUrl.replace(/\/$/, '');
    this.sid = null;
  }

  async call(method, path, body) {
    const res = await fetch(this.base + path, {
      method,
      headers: { 'content-type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(120000),
    });
    const text = await res.text();
    let json = {};
    try { json = JSON.parse(text); } catch (_) { /* non-JSON reply: keep empty */ }
    if (!res.ok) {
      const err = new Error(`${method} ${path} failed: ${(json.value && json.value.error) || res.status}`);
      err.webdriverError = json.value && json.value.error;
      throw err;
    }
    return json.value;
  }

  async createSession(alwaysMatch) {
    const v = await this.call('POST', '/session', { capabilities: { alwaysMatch, firstMatch: [{}] } });
    this.sid = v.sessionId;
  }

  async deleteSession() {
    if (this.sid) {
      await this.call('DELETE', `/session/${this.sid}`);
      this.sid = null;
    }
  }

  // Returns the element id, or null when the UiAutomator selector matches nothing.
  async find(selector) {
    try {
      const v = await this.call('POST', `/session/${this.sid}/element`, { using: '-android uiautomator', value: selector });
      return v[ELEMENT_KEY];
    } catch (e) {
      if (e.webdriverError === 'no such element') return null;
      throw e;
    }
  }

  click(el) { return this.call('POST', `/session/${this.sid}/element/${el}/click`, {}); }
  clear(el) { return this.call('POST', `/session/${this.sid}/element/${el}/clear`, {}); }
  sendKeys(el, text) { return this.call('POST', `/session/${this.sid}/element/${el}/value`, { text }); }
}

module.exports = { Appium };
