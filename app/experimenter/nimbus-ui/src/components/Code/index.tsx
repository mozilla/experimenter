/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import JSONPretty from "react-json-pretty";
import "../../styles/react-json-pretty-theme.scss";

export const Code = ({ codeString }: { codeString: string }) => {
  try {
    JSON.parse(codeString);
  } catch (e) {
    return (
      <pre className="mb-0 code-color">
        <code>{codeString}</code>
      </pre>
    );
  }
  return <JSONPretty data={codeString} />;
};
