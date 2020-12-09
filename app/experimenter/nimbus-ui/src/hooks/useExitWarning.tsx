/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useEffect, useState } from "react";

/**
 * Hook to trigger a browser dialog when a user attempts to exit the page.
 *
 * Example:
 *
 * const shouldWarnOnExit = useExitWarning();
 * return (
 *   <form>
 *     // The user made some important change that
 *     // should be saved before exiting
 *     <button onClick={() => {
 *       shouldWarnOnExit(true)
 *     }}>Change something important</button>
 *
 *     // The user decides to reset the changes they made
 *     <button onClick={() => {
 *       resetFields();
 *       shouldWarnOnExit(false);
 *     }}>Reset changes</button>
 *   </form>
 * );
 */

export const exitMessage =
  "You have unsaved Experiment changes. Are you sure you want to leave?";

export const exitHandler = (event: BeforeUnloadEvent) => {
  event.preventDefault();

  // Some browsers support custom message,
  // but for others these are just `true`
  event.returnValue = exitMessage;
  return exitMessage;
};

export function useExitWarning(init = false): () => void {
  const [warnOnExit, setWarnOnExit] = useState<boolean>(init);

  useEffect(() => {
    warnOnExit
      ? window.addEventListener("beforeunload", exitHandler)
      : window.removeEventListener("beforeunload", exitHandler);
  }, [warnOnExit]);

  return setWarnOnExit;
}
