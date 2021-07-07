/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import Logger from "./logger";

type ValueOf<T> = T[keyof T];
const loggerMethodNames = ["info", "trace", "warn", "error"] as const;

describe("services/logger", () => {
  let logger: Logger;

  describe("constructor", () => {
    it("should create logger with expected methods", () => {
      logger = new Logger();
      for (const loggerMethodName of loggerMethodNames) {
        expect(typeof logger[loggerMethodName]).toEqual("function");
      }
    });
  });

  loggerMethodNames.forEach((loggerMethodName) => {
    describe(loggerMethodName, () => {
      const windowLogMethod = loggerMethodName;
      let origMethod: ValueOf<typeof global.console>;
      let mockMethod: jest.Mock<any, any>;

      beforeEach(() => {
        origMethod = global.console[windowLogMethod];
        mockMethod = jest.fn();
        global.console[windowLogMethod] = mockMethod as typeof origMethod;
      });

      afterEach(() => {
        global.console[windowLogMethod] = origMethod;
      });

      it(`should use expected window.console.${windowLogMethod}`, () => {
        const msg = `log message for ${loggerMethodName}`;
        logger[loggerMethodName](msg);
        expect(mockMethod).toHaveBeenCalledWith(msg);
      });

      if (loggerMethodName === "error") {
        it("should do nothing if error method is missing", () => {
          // @ts-ignore next
          global.console.error = null;
          logger.error("this should be ignored");
          expect(mockMethod).not.toHaveBeenCalled();
        });

        it("should log from object", () => {
          const error = {
            message: "something went wrong",
            errorModule: {
              toInterpolatedMessage: jest.fn(() => "whew"),
            },
          };
          logger.error(error);
          expect(error.errorModule.toInterpolatedMessage).toHaveBeenCalledWith(
            error,
          );
          expect(mockMethod).toHaveBeenCalledWith("whew");
        });
      }
    });
  });
});
