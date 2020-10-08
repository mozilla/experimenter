/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import config, {
  getDefault,
  readConfig,
  decode,
  reset,
  update,
} from './config';

beforeEach(reset);

describe('readConfig', () => {
  it('merges the returned meta tag content value with the config', () => {
    const data = {
      version: '1.2.3'
    }

    const el = document.createElement('div');
    el.dataset.config = encodeURIComponent(JSON.stringify(data))

    readConfig(el);

    expect(config.version).toBeDefined();
    expect(config.version).toStrictEqual(data.version);
  });
});

describe('decode', () => {
  it('converts a JSON-stringified, URI-encoded string to a proper object', () => {
    const data = {
      decimated: 'dreams',
    };

    const encodedData = encodeURIComponent(JSON.stringify(data));
    const decodedData = decode(encodedData);

    expect(decodedData).toStrictEqual(data);
  });

  describe('development', () => {
    beforeAll(() => {
      Object.defineProperty(process.env, 'NODE_ENV', { value: 'development' });
      window.console.warn = jest.fn();
    });

    it('warns when server config is missing', () => {
      decode();
      expect(window.console.warn).toHaveBeenCalledWith(
        'Nimbus is missing server config'
      );
    });

    it('warns when an invalid server config is supplied', () => {
      decode('thou shalt not decode');
      expect(window.console.warn).toHaveBeenCalledWith(
        'Nimbus server config is invalid'
      );
    });
  });

  describe('production', () => {
    beforeAll(() => {
      Object.defineProperty(process.env, 'NODE_ENV', { value: 'production' });
    });

    it('warns when server config is missing', () => {
      expect(() => decode()).toThrowError('Configuration is empty');
    });

    it('warns when an invalid server config is supplied', () => {
      const decodingValue = 'not gonna happen';
      expect(() => decode(decodingValue)).toThrowError(
        `Invalid configuration "${decodingValue}": ${decodingValue}`
      );
    });
  });
});

describe('update', () => {
  it('recursively updates the config', () => {
    expect(config.sentry_dsn).toBeDefined();
    const oldSentryDsn = config.sentry_dsn;

    const newData = {
      sentry_dsn: 'http://sentry-rulez.net',
    };
    update(newData);

    expect(config.sentry_dsn).not.toStrictEqual(oldSentryDsn);
    expect(config.sentry_dsn).toStrictEqual(newData.sentry_dsn);
  });
});

describe('reset', () => {
  it('resets to the default config values', () => {
    const initialConfig = getDefault();
    expect(config).toStrictEqual(initialConfig);

    const newSentryDsn = 'http://sentry-rulez.net';
    update({ sentry_dsn: newSentryDsn });
    expect(config.sentry_dsn).toStrictEqual(newSentryDsn);

    reset();
    expect(config.sentry_dsn).not.toStrictEqual(newSentryDsn);
    expect(config).toStrictEqual(initialConfig);
  });

  it('removes any keys that are not in the default config', () => {
    expect(config).not.toHaveProperty('foo');

    const newData = {
      foo: 'bar',
    };
    update(newData);
    expect(config).toHaveProperty('foo');

    reset();
    expect(config).not.toHaveProperty('foo');
  });
});
