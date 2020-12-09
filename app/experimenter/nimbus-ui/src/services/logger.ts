/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/**
 * Constructor of log module.
 *
 * @param {Object} console Console object used for logging.
 *
 * @constructor
 */
class Logger {
  private _console: Console;

  constructor(console: Console = window.console) {
    this._console = console;
  }

  /**
   * Wrapper for `console.info` function that checks for availability and
   * then prints info.
   *
   */
  info(...args: any) {
    this._console?.info(...args);
  }

  /**
   * Wrapper for `console.trace` function that checks for availability and then prints
   * trace.
   *
   */
  trace(...args: any) {
    this._console?.trace(...args);
  }

  /**
   * Wrapper for `console.warn` function that checks for availability and
   * then prints warn.
   *
   */
  warn(...args: any) {
    this._console?.warn(...args);
  }

  /**
   * Wrapper for `console.error` function that checks for availability and interpolates
   * error messages if a translation exists.
   *
   * @param {Error} error Error object with optional errorModule.
   */
  error(...args: any) {
    if (this._console?.error) {
      let errorMessage = "";

      // If error module is present, attempt to interpolate string, else use error object message
      if (args[0]?.errorModule) {
        const error = args[0];
        errorMessage = error.errorModule.toInterpolatedMessage(error);
        this._console.error(errorMessage);
      } else {
        // Use regular console.error
        this._console.error(...args);
      }
    }
  }
}

export default Logger;
