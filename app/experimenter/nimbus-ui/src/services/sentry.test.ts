/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import * as Sentry from "@sentry/browser";
import sentryMetrics, { _Sentry } from "./sentry";

const dsn = "https://public:private@host:port/1";
type ValueOf<T> = T[keyof T];
const loggerMethodNames = ["info", "trace", "warn", "error"] as const;

describe("services/sentry", () => {
  const origMethods: { [name: string]: ValueOf<typeof global.console> } = {};

  beforeEach(() => {
    // Reduce console log noise in test output
    loggerMethodNames.forEach((name) => {
      origMethods[name] = global.console[name];
      global.console[name] = jest.fn();
    });
  });

  afterEach(() => {
    loggerMethodNames.forEach((name) => {
      global.console[name] = origMethods[name];
    });
  });

  describe("configure", () => {
    let sentryInit: jest.SpyInstance;

    beforeEach(() => {
      sentryInit = jest.spyOn(_Sentry, "init").mockImplementation(() => {});
    });

    afterEach(() => {
      sentryInit.mockRestore();
    });

    it("properly configures with dsn", () => {
      let errThrown = null;
      try {
        sentryMetrics.configure(dsn);
      } catch (e) {
        errThrown = e;
      }
      expect(errThrown).toBeNull();
      expect(sentryInit).toHaveBeenCalled();
      expect(global.console.error).not.toHaveBeenCalled();
    });

    it("logs an error without dsn", () => {
      let errThrown = null;
      try {
        // @ts-ignore
        sentryMetrics.configure(null);
      } catch (e) {
        errThrown = e;
      }
      expect(errThrown).toBeNull();
      expect(sentryInit).not.toHaveBeenCalled();
      expect(global.console.error).toHaveBeenCalled();
    });
  });

  describe("beforeSend", () => {
    beforeEach(() => {
      sentryMetrics.configure(dsn);
    });

    it("works without request url", () => {
      const data = {
        key: "value",
      } as Sentry.Event;

      const resultData = sentryMetrics.__beforeSend(data);

      expect(data).toEqual(resultData);
    });

    it("fingerprints errno", () => {
      const data = {
        request: {
          url: "https://example.com",
        },
        tags: {
          errno: "100",
        },
      } as Sentry.Event;

      const resultData = sentryMetrics.__beforeSend(data);

      expect(resultData.fingerprint![0]).toEqual("errno100");
      expect(resultData.level).toEqual(Sentry.Severity.Info);
    });

    it("properly erases sensitive information from url", () => {
      const url = "https://accounts.firefox.com/complete_reset_password";
      const badQuery =
        "?token=foo&code=bar&email=some%40restmail.net&service=sync";
      const goodQuery = "?token=VALUE&code=VALUE&email=VALUE&service=sync";
      const badData = {
        request: {
          url: url + badQuery,
        },
      };

      const goodData = {
        request: {
          url: url + goodQuery,
        },
      };

      const resultData = sentryMetrics.__beforeSend(badData);
      expect(resultData.request!.url).toEqual(goodData.request.url);
    });

    it("properly erases sensitive information from referrer", () => {
      const url = "https://accounts.firefox.com/complete_reset_password";
      const badQuery =
        "?token=foo&code=bar&email=some%40restmail.net&service=sync";
      const goodQuery = "?token=VALUE&code=VALUE&email=VALUE&service=sync";
      const badData = {
        request: {
          headers: {
            Referer: url + badQuery,
          },
        },
      };

      const goodData = {
        request: {
          headers: {
            Referer: url + goodQuery,
          },
        },
      };

      const resultData = sentryMetrics.__beforeSend(badData);
      expect(resultData.request?.headers?.Referer).toEqual(
        goodData.request.headers.Referer,
      );
    });

    it("properly erases sensitive information from abs_path", () => {
      const url = "https://accounts.firefox.com/complete_reset_password";
      const badCulprit =
        "https://accounts.firefox.com/scripts/57f6d4e4.main.js";
      const badAbsPath =
        "https://accounts.firefox.com/complete_reset_password?token=foo&code=bar&email=a@a.com&service=sync&resume=barbar";
      const goodAbsPath =
        "https://accounts.firefox.com/complete_reset_password?token=VALUE&code=VALUE&email=VALUE&service=sync&resume=VALUE";
      const data = {
        culprit: badCulprit,
        exception: {
          values: [
            {
              stacktrace: {
                frames: [
                  {
                    abs_path: badAbsPath, // eslint-disable-line camelcase
                  },
                  {
                    abs_path: badAbsPath, // eslint-disable-line camelcase
                  },
                ],
              },
            },
          ],
        },
        request: {
          url,
        },
      };

      const resultData = sentryMetrics.__beforeSend(data);

      expect(
        resultData.exception!.values![0].stacktrace!.frames![0].abs_path,
      ).toEqual(goodAbsPath);
      expect(
        resultData.exception!.values![0].stacktrace!.frames![1].abs_path,
      ).toEqual(goodAbsPath);
    });

    it("properly ignores some unexpected data structure in exception", () => {
      const url = "https://accounts.firefox.com/complete_reset_password";
      const badCulprit =
        "https://accounts.firefox.com/scripts/57f6d4e4.main.js";
      const data = {
        culprit: badCulprit,
        exception: {
          values: [
            {
              stacktrace: {
                frames: [{}],
              },
            },
            {
              stacktrace: {},
            },
          ],
        },
        request: {
          url,
        },
      };
      const resultData = sentryMetrics.__beforeSend(data);
      expect(resultData).toEqual(data);
    });
  });

  describe("cleanUpQueryParam", () => {
    it("properly erases sensitive information", () => {
      const fixtureUrl =
        "https://accounts.firefox.com/complete_reset_password?token=foo&code=bar&email=some%40restmail.net";
      const expectedUrl =
        "https://accounts.firefox.com/complete_reset_password?token=VALUE&code=VALUE&email=VALUE";
      const resultUrl = sentryMetrics.__cleanUpQueryParam(fixtureUrl);

      expect(resultUrl).toEqual(expectedUrl);
    });

    it("properly erases sensitive information, keeps allowed fields", () => {
      const fixtureUrl =
        "https://accounts.firefox.com/signup?client_id=foo&service=sync";
      const expectedUrl =
        "https://accounts.firefox.com/signup?client_id=foo&service=sync";
      const resultUrl = sentryMetrics.__cleanUpQueryParam(fixtureUrl);

      expect(resultUrl).toEqual(expectedUrl);
    });

    it("properly returns the url when there is no query", () => {
      const expectedUrl = "https://accounts.firefox.com/signup";
      const resultUrl = sentryMetrics.__cleanUpQueryParam(expectedUrl);

      expect(resultUrl).toEqual(expectedUrl);
    });
  });

  describe("captureException", () => {
    let sentryCaptureException: jest.SpyInstance;

    beforeEach(() => {
      sentryCaptureException = jest
        .spyOn(_Sentry, "captureException")
        .mockImplementation(() => "");
    });

    afterEach(() => {
      sentryCaptureException.mockRestore();
    });

    it("calls Sentry.captureException", () => {
      const error = new Error("testo");
      sentryMetrics.captureException(error);
      expect(sentryCaptureException).toHaveBeenCalled();
    });

    it("handles error tags with errno", () => {
      const error = new Error("testo");
      Object.assign(error, { errno: 110 });
      sentryMetrics.captureException(error);
      expect(sentryCaptureException).toHaveBeenCalled();
    });
  });
});
